#!/usr/bin/env python3
"""
Celery Monitor for Vigia Medical Pipeline
=========================================

Monitor de tareas Celery con métricas específicas para el contexto médico
y alertas automáticas para garantizar continuidad del servicio.
"""

import time
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List
from vigia_detect.core.celery_config import celery_app
from vigia_detect.utils.secure_logger import SecureLogger

logger = SecureLogger(__name__)

class CeleryMedicalMonitor:
    """Monitor especializado para tareas médicas de Celery"""
    
    def __init__(self):
        self.logger = SecureLogger(__name__)
        
        # Métricas críticas para contexto médico
        self.critical_queues = ['medical_priority', 'image_processing']
        self.warning_thresholds = {
            'queue_length': 10,      # Más de 10 tareas pendientes
            'task_failure_rate': 0.1, # Más de 10% fallos
            'avg_processing_time': 180, # Más de 3 minutos promedio
            'worker_count': 1        # Menos de 1 worker activo
        }
        
    def get_queue_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de todas las colas"""
        try:
            # Inspeccionar estado de Celery
            inspect = celery_app.control.inspect()
            
            # Obtener estadísticas de colas
            active_queues = inspect.active_queues()
            stats = inspect.stats()
            
            queue_stats = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'queues': {},
                'workers': {},
                'overall_health': 'healthy'
            }
            
            # Procesar estadísticas por worker
            if stats:
                for worker, worker_stats in stats.items():
                    queue_stats['workers'][worker] = {
                        'total_tasks': worker_stats.get('total', {}),
                        'pool_size': worker_stats.get('pool', {}).get('max-concurrency', 0),
                        'processes': worker_stats.get('pool', {}).get('processes', [])
                    }
            
            # Verificar colas activas
            if active_queues:
                for worker, queues in active_queues.items():
                    for queue_info in queues:
                        queue_name = queue_info.get('name', 'unknown')
                        if queue_name not in queue_stats['queues']:
                            queue_stats['queues'][queue_name] = {
                                'workers': [],
                                'routing_key': queue_info.get('routing_key'),
                                'is_critical': queue_name in self.critical_queues
                            }
                        queue_stats['queues'][queue_name]['workers'].append(worker)
            
            # Evaluar salud general
            queue_stats['overall_health'] = self._assess_overall_health(queue_stats)
            
            return queue_stats
            
        except Exception as e:
            self.logger.error(f"Failed to get queue stats: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'overall_health': 'critical'
            }
    
    def get_task_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de tareas médicas"""
        try:
            inspect = celery_app.control.inspect()
            
            # Tareas activas
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            task_metrics = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'active_tasks': 0,
                'scheduled_tasks': 0,
                'reserved_tasks': 0,
                'medical_tasks': 0,
                'critical_tasks': 0,
                'task_details': []
            }
            
            # Procesar tareas activas
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    for task in tasks:
                        task_metrics['active_tasks'] += 1
                        
                        task_name = task.get('name', 'unknown')
                        if 'medical' in task_name.lower():
                            task_metrics['medical_tasks'] += 1
                        if any(queue in task_name.lower() for queue in self.critical_queues):
                            task_metrics['critical_tasks'] += 1
                        
                        task_metrics['task_details'].append({
                            'worker': worker,
                            'task_id': task.get('id'),
                            'task_name': task_name,
                            'args': task.get('args', []),
                            'time_start': task.get('time_start')
                        })
            
            # Procesar tareas programadas
            if scheduled_tasks:
                for worker, tasks in scheduled_tasks.items():
                    task_metrics['scheduled_tasks'] += len(tasks)
            
            # Procesar tareas reservadas
            if reserved_tasks:
                for worker, tasks in reserved_tasks.items():
                    task_metrics['reserved_tasks'] += len(tasks)
            
            return task_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get task metrics: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }
    
    def check_medical_pipeline_health(self) -> Dict[str, Any]:
        """Verifica salud específica del pipeline médico"""
        health_check = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'alerts': [],
            'recommendations': []
        }
        
        try:
            # 1. Verificar conexión Redis
            try:
                result = celery_app.control.ping(timeout=5)
                if result:
                    health_check['checks']['redis_connection'] = 'healthy'
                else:
                    health_check['checks']['redis_connection'] = 'failed'
                    health_check['alerts'].append('Redis connection failed')
                    health_check['overall_status'] = 'critical'
            except Exception as e:
                health_check['checks']['redis_connection'] = 'failed'
                health_check['alerts'].append(f'Redis ping failed: {e}')
                health_check['overall_status'] = 'critical'
            
            # 2. Verificar workers activos
            stats = self.get_queue_stats()
            worker_count = len(stats.get('workers', {}))
            
            health_check['checks']['worker_count'] = worker_count
            if worker_count < self.warning_thresholds['worker_count']:
                health_check['alerts'].append(f'Low worker count: {worker_count}')
                health_check['recommendations'].append('Start additional Celery workers')
                health_check['overall_status'] = 'warning'
            
            # 3. Verificar colas críticas
            queue_stats = stats.get('queues', {})
            for critical_queue in self.critical_queues:
                if critical_queue not in queue_stats:
                    health_check['alerts'].append(f'Critical queue not found: {critical_queue}')
                    health_check['overall_status'] = 'critical'
                else:
                    health_check['checks'][f'queue_{critical_queue}'] = 'active'
            
            # 4. Verificar métricas de tareas
            task_metrics = self.get_task_metrics()
            active_medical_tasks = task_metrics.get('medical_tasks', 0)
            
            health_check['checks']['active_medical_tasks'] = active_medical_tasks
            if active_medical_tasks > 20:  # Muchas tareas médicas activas
                health_check['alerts'].append(f'High medical task load: {active_medical_tasks}')
                health_check['recommendations'].append('Consider scaling workers')
                health_check['overall_status'] = 'warning'
            
        except Exception as e:
            health_check['checks']['health_check_error'] = str(e)
            health_check['overall_status'] = 'critical'
            health_check['alerts'].append(f'Health check failed: {e}')
        
        return health_check
    
    def _assess_overall_health(self, queue_stats: Dict[str, Any]) -> str:
        """Evalúa salud general basada en estadísticas"""
        worker_count = len(queue_stats.get('workers', {}))
        
        if worker_count == 0:
            return 'critical'
        elif worker_count < self.warning_thresholds['worker_count']:
            return 'warning'
        else:
            return 'healthy'
    
    def run_continuous_monitor(self, interval: int = 30):
        """Ejecuta monitor continuo con intervalo especificado"""
        self.logger.info(f"Starting continuous medical pipeline monitor (interval: {interval}s)")
        
        try:
            while True:
                # Verificar salud del pipeline
                health_status = self.check_medical_pipeline_health()
                
                # Log según estado de salud
                if health_status['overall_status'] == 'critical':
                    self.logger.critical(
                        "MEDICAL PIPELINE CRITICAL",
                        extra={
                            'health_status': health_status,
                            'alerts': health_status['alerts']
                        }
                    )
                elif health_status['overall_status'] == 'warning':
                    self.logger.warning(
                        "Medical pipeline warning",
                        extra={
                            'health_status': health_status,
                            'alerts': health_status['alerts']
                        }
                    )
                else:
                    self.logger.info("Medical pipeline healthy")
                
                # Imprimir resumen
                print(f"\n🏥 Vigia Medical Pipeline Status - {health_status['timestamp']}")
                print(f"Overall Status: {health_status['overall_status'].upper()}")
                
                if health_status['alerts']:
                    print("🚨 Alerts:")
                    for alert in health_status['alerts']:
                        print(f"   - {alert}")
                
                if health_status['recommendations']:
                    print("💡 Recommendations:")
                    for rec in health_status['recommendations']:
                        print(f"   - {rec}")
                
                # Esperar próximo ciclo
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitor stopped by user")
            print("\n👋 Monitor detenido")
        except Exception as e:
            self.logger.error(f"Monitor error: {e}")
            print(f"\n❌ Error en monitor: {e}")

def main():
    """Función principal del monitor"""
    parser = argparse.ArgumentParser(description='Vigia Medical Pipeline Monitor')
    parser.add_argument('--interval', type=int, default=30, help='Monitor interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    
    args = parser.parse_args()
    
    monitor = CeleryMedicalMonitor()
    
    if args.once:
        # Ejecutar una vez
        health_status = monitor.check_medical_pipeline_health()
        
        if args.json:
            print(json.dumps(health_status, indent=2))
        else:
            print(f"Pipeline Status: {health_status['overall_status']}")
            if health_status['alerts']:
                print("Alerts:", health_status['alerts'])
    else:
        # Monitor continuo
        monitor.run_continuous_monitor(args.interval)

if __name__ == '__main__':
    main()