#!/usr/bin/env python3
"""
Test temporal de MedGemma - SOLO PARA PRUEBAS
IMPORTANTE: Usar API keys en código es INSEGURO. Usa variables de entorno en producción.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# ADVERTENCIA: NUNCA hagas esto en producción
# Configura temporalmente la API key (ELIMINAR DESPUÉS DE PROBAR)
os.environ['GOOGLE_API_KEY'] = input("Ingresa tu API key de Google (será temporal): ").strip()

from vigia_detect.ai.medgemma_client import MedGemmaClient, MedicalContext

async def test_medgemma():
    """Prueba rápida de MedGemma"""
    try:
        print("🧠 Probando MedGemma...")
        
        client = MedGemmaClient()
        
        # Caso simple de prueba
        result = await client.analyze_lpp_findings(
            clinical_observations="Paciente con eritema no blanqueable en región sacra de 3cm",
            medical_context=MedicalContext(patient_age=75)
        )
        
        if result:
            print("✅ MedGemma funcionando correctamente!")
            print(f"Confianza: {result.confidence_score:.2%}")
            print(f"Hallazgos: {result.clinical_findings}")
        else:
            print("❌ No se obtuvo respuesta")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("⚠️  ADVERTENCIA: Este script es solo para pruebas")
    print("En producción, usa variables de entorno desde .env")
    print("-" * 50)
    
    asyncio.run(test_medgemma())
    
    # Limpiar la variable de entorno
    if 'GOOGLE_API_KEY' in os.environ:
        del os.environ['GOOGLE_API_KEY']
    
    print("\n✅ API key temporal eliminada de memoria")