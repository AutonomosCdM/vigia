#!/usr/bin/env python3
"""
Script para probar el webhook de WhatsApp en Render
"""
import requests

# Datos del webhook simulado de WhatsApp
webhook_data = {
    'From': 'whatsapp:+56912345678',
    'Body': 'Imagen para analizar',
    'NumMedia': '1',
    'MediaUrl0': 'https://httpbin.org/image/jpeg',
    'MediaContentType0': 'image/jpeg'
}

url = 'https://vigia-whatsapp.onrender.com/webhook/whatsapp'

print(f"Enviando webhook simulado a {url}")
print(f"Datos: {webhook_data}")

try:
    response = requests.post(
        url,
        data=webhook_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")