#!/usr/bin/env python3
"""
Script para migrar todos los imports de lpp_detect a vigia_detect
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Corrige los imports en un archivo específico."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar todos los imports de lpp_detect por vigia_detect
        original_content = content
        content = re.sub(r'from lpp_detect\.', 'from vigia_detect.', content)
        content = re.sub(r'import lpp_detect\.', 'import vigia_detect.', content)
        content = re.sub(r'import lpp_detect\b', 'import vigia_detect', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Actualizado: {file_path}")
            return True
        else:
            print(f"  Sin cambios: {file_path}")
            return False
    except Exception as e:
        print(f"✗ Error en {file_path}: {e}")
        return False

def main():
    """Busca y corrige todos los archivos Python con imports de lpp_detect."""
    project_root = Path(__file__).parent.parent
    files_updated = 0
    files_checked = 0
    
    # Lista de archivos a actualizar
    files_to_update = [
        "examples/mensaje_demo.py",
        "examples/caso_real_demo.py",
        "examples/modal_demo.py",
        "examples/workflow_completo.py",
        "examples/boton_modal_demo.py",
        "vigia_detect/run_whatsapp.py",
        "vigia_detect/test_slack.py",
        "vigia_detect/test_workflow.py",
        "vigia_detect/messaging/tests/test_whatsapp_templates.py",
        "vigia_detect/messaging/tests/test_whatsapp_server.py",
        "vigia_detect/messaging/tests/test_whatsapp_processor.py",
        "vigia_detect/messaging/tests/test_twilio_client.py",
        "vigia_detect/messaging/utils/test_twilio.py",
        "vigia_detect/messaging/utils/__init__.py",
        "vigia_detect/messaging/templates/__init__.py",
        "vigia_detect/messaging/whatsapp/tests/test_processor.py",
        "vigia_detect/redis_layer/tests/test_vector_service.py",
        "vigia_detect/redis_layer/tests/test_cache_service.py",
        "apps/enfermera_ui/app.py"
    ]
    
    print("🔧 Iniciando migración de imports de lpp_detect a vigia_detect...\n")
    
    for file_path in files_to_update:
        full_path = project_root / file_path
        if full_path.exists():
            files_checked += 1
            if fix_imports_in_file(full_path):
                files_updated += 1
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")
    
    print(f"\n✅ Migración completada:")
    print(f"   - Archivos revisados: {files_checked}")
    print(f"   - Archivos actualizados: {files_updated}")

if __name__ == "__main__":
    main()