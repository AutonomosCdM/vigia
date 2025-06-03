#!/usr/bin/env python3
"""
Test webhook con datos simples para debuggear
"""
import requests

# Test 1: Webhook sin imagen (debería responder con comando no reconocido)
print("=== Test 1: Mensaje de texto ===")
response = requests.post(
    'https://vigia-whatsapp.onrender.com/webhook/whatsapp',
    data={
        'From': 'whatsapp:+56912345678',
        'Body': 'Hola',
        'NumMedia': '0'
    },
    timeout=30
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

print("\n=== Test 2: Health check ===")
response = requests.get('https://vigia-whatsapp.onrender.com/health')
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

print("\n=== Test 3: Webhook con imagen (el que falla) ===")
response = requests.post(
    'https://vigia-whatsapp.onrender.com/webhook/whatsapp',
    data={
        'From': 'whatsapp:+56912345678',
        'Body': 'Imagen para analizar',
        'NumMedia': '1',
        'MediaUrl0': 'https://httpbin.org/image/jpeg',
        'MediaContentType0': 'image/jpeg'
    },
    timeout=30
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")