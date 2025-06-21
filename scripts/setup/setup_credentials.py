#!/usr/bin/env python3
"""
Script para gestionar credenciales del proyecto Vigia de forma segura.
Almacena las credenciales en el keychain del sistema.
"""

import os
import sys
import json
import getpass
from pathlib import Path

try:
    import keyring
except ImportError:
    print("Instalando keyring para almacenamiento seguro...")
    os.system(f"{sys.executable} -m pip install keyring")
    import keyring

# Servicio para el keychain
SERVICE_NAME = "vigia-project"

# Credenciales requeridas
CREDENTIALS = {
    "TWILIO_ACCOUNT_SID": "Twilio Account SID",
    "TWILIO_AUTH_TOKEN": "Twilio Auth Token", 
    "TWILIO_WHATSAPP_FROM": "Twilio WhatsApp Number (formato: whatsapp:+1234567890)",
    "ANTHROPIC_API_KEY": "Anthropic API Key",
    "SUPABASE_URL": "Supabase Project URL",
    "SUPABASE_KEY": "Supabase Anon Key"
}

def store_credential(key: str, value: str):
    """Almacena una credencial en el keychain del sistema."""
    keyring.set_password(SERVICE_NAME, key, value)
    print(f"✅ {key} almacenada de forma segura")

def get_credential(key: str) -> str:
    """Obtiene una credencial del keychain."""
    return keyring.get_password(SERVICE_NAME, key)

def setup_credentials():
    """Configura todas las credenciales del proyecto."""
    print("🔐 Configuración de Credenciales para Vigia")
    print("=" * 50)
    print("Las credenciales se almacenarán de forma segura en tu keychain")
    print()
    
    for key, description in CREDENTIALS.items():
        current = get_credential(key)
        if current:
            print(f"\n{key} ya está configurada")
            update = input("¿Deseas actualizarla? (s/N): ").lower()
            if update != 's':
                continue
        
        print(f"\n{description}:")
        if "TOKEN" in key or "KEY" in key:
            value = getpass.getpass("Valor (oculto): ")
        else:
            value = input("Valor: ")
        
        if value:
            store_credential(key, value)

def export_to_env():
    """Exporta las credenciales a un archivo .env.local."""
    env_file = Path(".env.local")
    
    print("\n📝 Exportando credenciales a .env.local...")
    
    lines = []
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in CREDENTIALS:
                    value = get_credential(key)
                    if value:
                        lines.append(f"{key}={value}\n")
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
            else:
                lines.append(line)
    
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print("✅ Credenciales exportadas a .env.local")

def show_credentials():
    """Muestra las credenciales configuradas (parcialmente ocultas)."""
    print("\n🔑 Credenciales Configuradas:")
    print("=" * 50)
    
    for key in CREDENTIALS:
        value = get_credential(key)
        if value:
            if "TOKEN" in key or "KEY" in key:
                # Mostrar solo los primeros y últimos caracteres
                if len(value) > 8:
                    masked = f"{value[:4]}...{value[-4:]}"
                else:
                    masked = "****"
                print(f"{key}: {masked}")
            else:
                print(f"{key}: {value}")
        else:
            print(f"{key}: ❌ No configurada")

def create_render_env():
    """Crea un archivo con las variables para Render."""
    print("\n📋 Generando configuración para Render...")
    
    render_env = []
    for key in CREDENTIALS:
        value = get_credential(key)
        if value:
            render_env.append(f"{key}={value}")
    
    with open("render_env.txt", "w") as f:
        f.write("\n".join(render_env))
    
    print("✅ Archivo render_env.txt creado")
    print("   Puedes copiar y pegar estas variables en Render")

def main():
    """Menú principal."""
    while True:
        print("\n🔐 Gestor de Credenciales - Vigia")
        print("=" * 50)
        print("1. Configurar credenciales")
        print("2. Ver credenciales configuradas")
        print("3. Exportar a .env.local")
        print("4. Generar archivo para Render")
        print("5. Salir")
        
        choice = input("\nSelecciona una opción (1-5): ")
        
        if choice == "1":
            setup_credentials()
        elif choice == "2":
            show_credentials()
        elif choice == "3":
            export_to_env()
        elif choice == "4":
            create_render_env()
        elif choice == "5":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    # Asegurar que estamos en el directorio del proyecto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    main()