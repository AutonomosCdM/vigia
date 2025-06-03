#!/usr/bin/env python3
"""
Test del servidor simple local
"""
import requests

# Test con imagen
print("=== Test servidor simple local ===")
response = requests.post(
    'http://localhost:5005/webhook/whatsapp',
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