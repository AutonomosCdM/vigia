#!/usr/bin/env python3
"""
🕐 Claude Time Tracker - Comparación Claude vs Humanos
Sistema de tracking automático para medir productividad
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import os

class ClaudeTimeTracker:
    """Tracker de tiempo para comparar Claude vs estimaciones humanas"""
    
    def __init__(self, project_root: str = "/Users/autonomos_dev/Projects/vigia"):
        self.project_root = Path(project_root)
        self.data_file = self.project_root / "data" / "claude_time_tracking.json"
        self.data_file.parent.mkdir(exist_ok=True)
        self.current_session = None
        
    def start_task(self, task_name: str, human_estimate_hours: float, 
                   description: str = "", priority: str = "medium") -> str:
        """Iniciar tracking de una tarea"""
        task_id = f"task_{int(time.time())}"
        
        task_data = {
            "task_id": task_id,
            "task_name": task_name,
            "description": description,
            "priority": priority,
            "human_estimate_hours": human_estimate_hours,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "claude_actual_hours": None,
            "efficiency_ratio": None,  # Claude time / Human estimate
            "status": "in_progress",
            "checkpoints": [],
            "notes": []
        }
        
        # Cargar datos existentes
        data = self._load_data()
        data["tasks"][task_id] = task_data
        data["stats"]["total_tasks"] += 1
        data["stats"]["active_tasks"] += 1
        
        self._save_data(data)
        self.current_session = task_id
        
        print(f"🚀 Iniciando tarea: {task_name}")
        print(f"📊 Estimación humana: {human_estimate_hours}h")
        print(f"🆔 Task ID: {task_id}")
        
        return task_id
    
    def add_checkpoint(self, message: str, task_id: Optional[str] = None):
        """Añadir checkpoint durante la tarea"""
        if not task_id:
            task_id = self.current_session
            
        if not task_id:
            print("❌ No hay tarea activa")
            return
            
        data = self._load_data()
        if task_id in data["tasks"]:
            checkpoint = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "elapsed_minutes": self._get_elapsed_minutes(task_id)
            }
            data["tasks"][task_id]["checkpoints"].append(checkpoint)
            self._save_data(data)
            print(f"✅ Checkpoint: {message} (Elapsed: {checkpoint['elapsed_minutes']:.1f}min)")
    
    def finish_task(self, task_id: Optional[str] = None, success: bool = True, 
                   notes: str = ""):
        """Finalizar tracking de tarea"""
        if not task_id:
            task_id = self.current_session
            
        if not task_id:
            print("❌ No hay tarea activa")
            return
            
        data = self._load_data()
        if task_id not in data["tasks"]:
            print(f"❌ Tarea {task_id} no encontrada")
            return
            
        task = data["tasks"][task_id]
        task["end_time"] = datetime.now().isoformat()
        task["status"] = "completed" if success else "failed"
        
        # Calcular tiempo real de Claude
        start_time = datetime.fromisoformat(task["start_time"])
        end_time = datetime.fromisoformat(task["end_time"])
        claude_actual_hours = (end_time - start_time).total_seconds() / 3600
        
        task["claude_actual_hours"] = claude_actual_hours
        task["efficiency_ratio"] = claude_actual_hours / task["human_estimate_hours"]
        
        if notes:
            task["notes"].append({
                "timestamp": datetime.now().isoformat(),
                "note": notes
            })
        
        # Actualizar estadísticas
        data["stats"]["active_tasks"] -= 1
        if success:
            data["stats"]["completed_tasks"] += 1
            data["stats"]["total_claude_hours"] += claude_actual_hours
            data["stats"]["total_human_estimate_hours"] += task["human_estimate_hours"]
        else:
            data["stats"]["failed_tasks"] += 1
            
        self._save_data(data)
        self.current_session = None
        
        # Mostrar resultados
        self._print_task_summary(task)
        
    def get_productivity_stats(self) -> Dict:
        """Obtener estadísticas de productividad"""
        data = self._load_data()
        stats = data["stats"]
        
        if stats["total_human_estimate_hours"] > 0:
            overall_efficiency = stats["total_claude_hours"] / stats["total_human_estimate_hours"]
        else:
            overall_efficiency = 0
            
        productivity_stats = {
            "overall_efficiency_ratio": overall_efficiency,
            "total_tasks": stats["total_tasks"],
            "completed_tasks": stats["completed_tasks"],
            "success_rate": stats["completed_tasks"] / max(stats["total_tasks"], 1) * 100,
            "average_claude_time": stats["total_claude_hours"] / max(stats["completed_tasks"], 1),
            "average_human_estimate": stats["total_human_estimate_hours"] / max(stats["total_tasks"], 1),
            "time_saved_hours": stats["total_human_estimate_hours"] - stats["total_claude_hours"],
            "productivity_multiplier": 1 / max(overall_efficiency, 0.01)
        }
        
        return productivity_stats
    
    def print_dashboard(self):
        """Mostrar dashboard de productividad"""
        stats = self.get_productivity_stats()
        
        print("\n" + "="*60)
        print("🤖 CLAUDE vs HUMAN PRODUCTIVITY DASHBOARD")
        print("="*60)
        print(f"📊 Total Tasks: {stats['total_tasks']}")
        print(f"✅ Completed: {stats['completed_tasks']}")
        print(f"📈 Success Rate: {stats['success_rate']:.1f}%")
        print(f"⚡ Efficiency Ratio: {stats['overall_efficiency_ratio']:.2f}")
        print(f"🚀 Productivity Multiplier: {stats['productivity_multiplier']:.1f}x")
        print(f"⏰ Average Claude Time: {stats['average_claude_time']:.1f}h")
        print(f"👤 Average Human Estimate: {stats['average_human_estimate']:.1f}h")
        print(f"💰 Time Saved: {stats['time_saved_hours']:.1f}h")
        
        if stats['overall_efficiency_ratio'] < 1:
            print(f"🏆 Claude is {stats['productivity_multiplier']:.1f}x FASTER than humans!")
        else:
            print(f"🐌 Claude is {stats['overall_efficiency_ratio']:.1f}x slower than humans")
            
        print("="*60)
    
    def _load_data(self) -> Dict:
        """Cargar datos de tracking"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "tasks": {},
                "stats": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "active_tasks": 0,
                    "total_claude_hours": 0.0,
                    "total_human_estimate_hours": 0.0
                }
            }
    
    def _save_data(self, data: Dict):
        """Guardar datos de tracking"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_elapsed_minutes(self, task_id: str) -> float:
        """Obtener minutos transcurridos desde inicio de tarea"""
        data = self._load_data()
        if task_id in data["tasks"]:
            start_time = datetime.fromisoformat(data["tasks"][task_id]["start_time"])
            return (datetime.now() - start_time).total_seconds() / 60
        return 0
    
    def _print_task_summary(self, task: Dict):
        """Mostrar resumen de tarea completada"""
        print("\n" + "="*50)
        print(f"🎯 TASK COMPLETED: {task['task_name']}")
        print("="*50)
        print(f"👤 Human Estimate: {task['human_estimate_hours']:.1f}h")
        print(f"🤖 Claude Actual: {task['claude_actual_hours']:.1f}h")
        print(f"⚡ Efficiency Ratio: {task['efficiency_ratio']:.2f}")
        
        if task['efficiency_ratio'] < 1:
            speedup = 1 / task['efficiency_ratio']
            print(f"🏆 Claude was {speedup:.1f}x FASTER!")
        else:
            print(f"🐌 Claude was {task['efficiency_ratio']:.1f}x slower")
            
        print(f"📝 Checkpoints: {len(task['checkpoints'])}")
        print("="*50)

def main():
    """CLI para Claude Time Tracker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Time Tracker")
    parser.add_argument("action", choices=["start", "checkpoint", "finish", "stats", "dashboard"])
    parser.add_argument("--task-name", help="Nombre de la tarea")
    parser.add_argument("--estimate", type=float, help="Estimación humana en horas")
    parser.add_argument("--message", help="Mensaje para checkpoint")
    parser.add_argument("--notes", help="Notas finales")
    parser.add_argument("--task-id", help="ID de tarea específica")
    
    args = parser.parse_args()
    tracker = ClaudeTimeTracker()
    
    if args.action == "start":
        if not args.task_name or not args.estimate:
            print("❌ Requiere --task-name y --estimate")
            return
        tracker.start_task(args.task_name, args.estimate)
        
    elif args.action == "checkpoint":
        if not args.message:
            print("❌ Requiere --message")
            return
        tracker.add_checkpoint(args.message, args.task_id)
        
    elif args.action == "finish":
        tracker.finish_task(args.task_id, notes=args.notes or "")
        
    elif args.action == "stats":
        stats = tracker.get_productivity_stats()
        print(json.dumps(stats, indent=2))
        
    elif args.action == "dashboard":
        tracker.print_dashboard()

if __name__ == "__main__":
    main()