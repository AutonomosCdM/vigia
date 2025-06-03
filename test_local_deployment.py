#!/usr/bin/env python3
"""
Script para probar el deployment local antes de Render
"""
import subprocess
import time
import requests
import json
import sys

def test_webhook_server():
    """Prueba el servidor webhook simple"""
    print("🔧 Iniciando servidor webhook...")
    
    # Iniciar el servidor
    server = subprocess.Popen(
        [sys.executable, "render_webhook_simple.py"],
        env={**subprocess.os.environ, "PORT": "8001"}
    )
    
    # Esperar a que inicie
    time.sleep(3)
    
    try:
        # Probar endpoint de salud
        print("\n📡 Probando endpoint /health...")
        resp = requests.get("http://localhost:8001/health")
        print(f"Respuesta: {resp.json()}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
        print("✅ Health check OK")
        
        # Probar webhook
        print("\n📡 Probando webhook...")
        test_data = {
            "event": "test",
            "patient_code": "TEST-2025-001",
            "detection": {
                "lesion_detected": True,
                "confidence": 0.95,
                "grade": 2
            }
        }
        
        resp = requests.post(
            "http://localhost:8001/webhook",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Respuesta: {json.dumps(resp.json(), indent=2)}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        print("✅ Webhook OK")
        
        print("\n✅ Todas las pruebas pasaron!")
        
    except Exception as e:
        print(f"\n❌ Error en pruebas: {e}")
        
    finally:
        # Terminar servidor
        server.terminate()
        server.wait()

def test_whatsapp_server():
    """Prueba el servidor WhatsApp"""
    print("\n🔧 Iniciando servidor WhatsApp...")
    
    # Iniciar el servidor
    server = subprocess.Popen(
        [sys.executable, "render_whatsapp.py"],
        env={**subprocess.os.environ, "PORT": "5001"}
    )
    
    # Esperar a que inicie
    time.sleep(3)
    
    try:
        # Probar endpoint de salud
        print("\n📡 Probando endpoint raíz...")
        resp = requests.get("http://localhost:5001/")
        print(f"Código de respuesta: {resp.status_code}")
        assert resp.status_code == 200
        print("✅ WhatsApp server OK")
        
    except Exception as e:
        print(f"\n❌ Error en pruebas: {e}")
        
    finally:
        # Terminar servidor
        server.terminate()
        server.wait()

if __name__ == "__main__":
    print("🚀 Pruebas de deployment local\n")
    
    # Probar webhook
    test_webhook_server()
    
    # Probar WhatsApp
    print("\n" + "="*50)
    test_whatsapp_server()
    
    print("\n✅ Listo para deployment en Render!")