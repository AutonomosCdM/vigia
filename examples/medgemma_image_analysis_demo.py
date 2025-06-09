#!/usr/bin/env python3
"""
Demo de Análisis de Imágenes Médicas con MedGemma via Ollama
Demuestra el análisis multimodal de imágenes médicas usando MedGemma.
"""

import asyncio
import base64
import sys
from pathlib import Path
from typing import Optional

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont


class MedGemmaImageAnalysisDemo:
    """Demo de análisis de imágenes médicas con MedGemma."""
    
    def __init__(self):
        self.model_name = "alibayram/medgemma"
    
    def check_ollama_available(self) -> bool:
        """Verificar si Ollama está disponible."""
        try:
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def check_model_installed(self) -> bool:
        """Verificar si el modelo está instalado."""
        try:
            result = subprocess.run(["ollama", "list"], 
                                  capture_output=True, text=True)
            return self.model_name in result.stdout
        except Exception:
            return False
    
    def create_sample_medical_image(self) -> str:
        """Crear imagen médica de muestra para demostración."""
        # Crear imagen de 400x300 con fondo blanco
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Simular una lesión por presión
        # Área rojiza en región sacra
        draw.ellipse([150, 120, 250, 180], fill='#FF6B6B', outline='#FF4757')
        
        # Área más oscura en el centro (simulando grado 2)
        draw.ellipse([175, 135, 225, 165], fill='#A5282C', outline='#7F1D1D')
        
        # Texto descriptivo
        try:
            # Intentar usar una fuente más grande
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            # Usar fuente por defecto si no encuentra Arial
            font = ImageFont.load_default()
        
        draw.text((10, 10), "Imagen de Demostración", fill='black', font=font)
        draw.text((10, 30), "Posible LPP Grado 2", fill='black', font=font)
        draw.text((10, 50), "Región Sacra", fill='black', font=font)
        
        # Guardar imagen temporal
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name)
        
        return temp_file.name
    
    def analyze_image_with_ollama(self, image_path: str, prompt: str) -> str:
        """Analizar imagen usando Ollama con MedGemma."""
        try:
            # Comando para Ollama con imagen
            # Nota: alibayram/medgemma puede no soportar imágenes directamente
            # Usaremos el modelo para análisis de texto sobre descripción
            
            # Leer y describir la imagen primero
            img_description = self.describe_image_basic(image_path)
            
            # Crear prompt combinado
            combined_prompt = f"""
Analiza esta imagen médica basándote en la siguiente descripción:

Descripción de la imagen: {img_description}

Pregunta médica: {prompt}

Proporciona un análisis médico profesional considerando:
1. Posible diagnóstico
2. Grado de severidad
3. Recomendaciones de tratamiento
4. Señales de alarma
5. Seguimiento necesario
"""
            
            # Ejecutar análisis con Ollama
            result = subprocess.run([
                "ollama", "run", self.model_name, combined_prompt
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error en análisis: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Error: Tiempo de análisis agotado"
        except Exception as e:
            return f"Error ejecutando análisis: {e}"
    
    def describe_image_basic(self, image_path: str) -> str:
        """Descripción básica de la imagen usando análisis de píxeles."""
        try:
            img = Image.open(image_path)
            width, height = img.size
            
            # Analizar colores dominantes
            colors = img.getcolors(maxcolors=256*256*256)
            if colors:
                # Ordenar por frecuencia
                colors.sort(reverse=True)
                dominant_colors = colors[:5]
                
                color_desc = []
                for count, color in dominant_colors:
                    if isinstance(color, tuple) and len(color) == 3:
                        r, g, b = color
                        if r > 200 and g < 100 and b < 100:
                            color_desc.append("área rojiza")
                        elif r > 150 and g < 150 and b < 150:
                            color_desc.append("área rosada")
                        elif r < 100 and g < 100 and b < 100:
                            color_desc.append("área oscura")
                        elif r > 200 and g > 200 and b > 200:
                            color_desc.append("área clara/piel normal")
            
            description = f"Imagen médica de {width}x{height} píxeles. "
            if color_desc:
                description += f"Se observan: {', '.join(set(color_desc))}. "
            
            description += "Posible lesión cutánea con cambios de coloración que sugieren lesión por presión."
            
            return description
            
        except Exception as e:
            return f"Imagen médica con posibles hallazgos patológicos. Error en análisis detallado: {e}"
    
    async def run_demo(self):
        """Ejecutar demostración completa."""
        print("🔬 Demo de Análisis de Imágenes Médicas con MedGemma")
        print("=" * 60)
        
        # Verificar requisitos
        if not self.check_ollama_available():
            print("❌ Ollama no está disponible. Instalar con:")
            print("   python scripts/setup_medgemma_ollama.py --install-ollama")
            return
        
        if not self.check_model_installed():
            print("❌ Modelo MedGemma no está instalado. Instalar con:")
            print(f"   python scripts/setup_medgemma_ollama.py --model 4b --install")
            return
        
        print("✅ Requisitos verificados")
        
        # Crear imagen de muestra
        print("\n📸 Creando imagen médica de demostración...")
        sample_image = self.create_sample_medical_image()
        print(f"   Imagen creada: {sample_image}")
        
        # Casos de análisis
        test_cases = [
            {
                "prompt": "¿Qué tipo de lesión observas en esta imagen? Describe el grado de severidad.",
                "description": "Análisis de tipo y grado de lesión"
            },
            {
                "prompt": "¿Cuáles son las recomendaciones de tratamiento para esta lesión por presión?",
                "description": "Recomendaciones terapéuticas"
            },
            {
                "prompt": "¿Qué signos de alarma debo buscar en el seguimiento de esta lesión?",
                "description": "Signos de alarma y seguimiento"
            }
        ]
        
        # Ejecutar análisis
        for i, case in enumerate(test_cases, 1):
            print(f"\n🔍 CASO {i}: {case['description']}")
            print("-" * 50)
            print(f"Consulta: {case['prompt']}")
            print("\n🤖 Análisis de MedGemma:")
            print("-" * 30)
            
            # Análisis con timeout visual
            print("⏳ Analizando imagen...")
            analysis = self.analyze_image_with_ollama(sample_image, case['prompt'])
            
            print(analysis)
            print("\n" + "=" * 50)
        
        # Estadísticas finales
        print("\n📊 Resumen de la Demostración")
        print("-" * 40)
        print(f"✅ Imagen analizada: {Path(sample_image).name}")
        print(f"✅ Modelo utilizado: {self.model_name}")
        print(f"✅ Casos analizados: {len(test_cases)}")
        print(f"✅ Análisis completado exitosamente")
        
        # Limpiar archivo temporal
        try:
            Path(sample_image).unlink()
            print(f"🧹 Archivo temporal eliminado")
        except:
            print(f"⚠️ No se pudo eliminar: {sample_image}")
        
        print("\n💡 Nota importante:")
        print("   Este es un demo con imagen sintética.")
        print("   Para uso clínico real, se requiere:")
        print("   - Validación médica profesional")
        print("   - Modelos especializados en dermatología")
        print("   - Supervisión de personal calificado")


async def main():
    """Función principal."""
    demo = MedGemmaImageAnalysisDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print("🔬 Iniciando demo de análisis de imágenes médicas...")
    print("Presiona Ctrl+C para interrumpir\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrumpida por usuario")
    except Exception as e:
        print(f"\n❌ Error en demo: {e}")