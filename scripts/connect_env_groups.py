#!/usr/bin/env python3
"""
Script para conectar Environment Groups a servicios usando la API de Render.
"""

import os
import sys
import requests
import json

# Configuración
RENDER_API_KEY = os.environ.get('RENDER_API_KEY')
if not RENDER_API_KEY:
    print("❌ Error: Necesitas configurar RENDER_API_KEY")
    print("   1. Ve a https://dashboard.render.com/u/settings#api-keys")
    print("   2. Crea un API key")
    print("   3. Ejecuta: export RENDER_API_KEY='tu-api-key'")
    sys.exit(1)

BASE_URL = "https://api.render.com/v1"
HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json"
}

def get_env_groups():
    """Obtener todos los environment groups."""
    response = requests.get(f"{BASE_URL}/env-groups", headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        # La API devuelve una lista de objetos con 'cursor' y 'envGroup'
        if isinstance(data, list):
            return [item['envGroup'] for item in data if 'envGroup' in item]
        else:
            print(f"⚠️  Estructura inesperada: {json.dumps(data, indent=2)}")
            return []
    else:
        print(f"❌ Error obteniendo env groups: {response.status_code}")
        print(response.text)
        return []

def get_services():
    """Obtener todos los servicios."""
    response = requests.get(f"{BASE_URL}/services", headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        # La API devuelve una lista de objetos con 'cursor' y 'service'
        if isinstance(data, list):
            return [item['service'] for item in data if 'service' in item]
        else:
            print(f"⚠️  Estructura inesperada: {json.dumps(data, indent=2)}")
            return []
    else:
        print(f"❌ Error obteniendo servicios: {response.status_code}")
        print(response.text)
        return []

def link_env_group_to_service(env_group_id, service_id):
    """Conectar un environment group a un servicio."""
    url = f"{BASE_URL}/env-groups/{env_group_id}/services/{service_id}"
    response = requests.post(url, headers=HEADERS)
    if response.status_code in [200, 201, 204]:
        return True
    else:
        print(f"❌ Error conectando env group: {response.status_code}")
        print(response.text)
        return False

def main():
    print("🔧 Conectando Environment Groups a Servicios de Vigia")
    print("=" * 60)
    
    # Obtener environment groups
    print("\n📦 Obteniendo Environment Groups...")
    env_groups = get_env_groups()
    
    # Mostrar todos los groups encontrados
    print(f"\n📋 Environment Groups encontrados: {len(env_groups)}")
    for group in env_groups:
        if isinstance(group, dict):
            print(f"   - {group.get('name', 'Sin nombre')} (ID: {group.get('id', 'N/A')})")
        else:
            print(f"   - Tipo inesperado: {type(group)}")
    
    # Buscar el grupo 'vigia'
    vigia_group = None
    for group in env_groups:
        if isinstance(group, dict) and group.get('name', '').lower() == 'vigia':
            vigia_group = group
            print(f"\n✅ Environment Group 'vigia' encontrado: {group.get('id')}")
            break
    
    if not vigia_group and env_groups:
        # Si no encontramos 'vigia' pero hay grupos, usar el primero
        vigia_group = env_groups[0] if isinstance(env_groups[0], dict) else None
        if vigia_group:
            print(f"\n⚠️  No se encontró 'vigia', usando: {vigia_group.get('name')} ({vigia_group.get('id')})")
        else:
            print("❌ No se pudo usar ningún Environment Group")
            sys.exit(1)
    elif not env_groups:
        print("❌ No hay Environment Groups disponibles")
        sys.exit(1)
    
    # Obtener servicios
    print("\n🚀 Obteniendo Servicios...")
    services = get_services()
    
    # Filtrar servicios de vigia
    vigia_services = [s for s in services if s.get('name', '').startswith('vigia-')]
    
    if not vigia_services:
        print("❌ No se encontraron servicios de Vigia")
        sys.exit(1)
    
    print(f"\n📋 Servicios encontrados:")
    for service in vigia_services:
        print(f"   - {service['name']} ({service['id']})")
    
    # Conectar environment group a cada servicio
    print(f"\n🔗 Conectando Environment Group 'vigia' a los servicios...")
    for service in vigia_services:
        print(f"\n   Conectando a {service['name']}...", end='')
        if link_env_group_to_service(vigia_group['id'], service['id']):
            print(" ✅")
        else:
            print(" ❌")
    
    print("\n✨ ¡Proceso completado!")
    print("   Los servicios ahora deberían tener acceso a las variables de entorno.")

if __name__ == "__main__":
    main()