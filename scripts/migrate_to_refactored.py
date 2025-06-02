#!/usr/bin/env python3
"""
Script de migración para facilitar la transición al código refactorizado.
Ayuda a actualizar imports y código existente.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Mapeo de imports antiguos a nuevos
IMPORT_MAPPINGS = {
    # Clientes
    'from vigia_detect.db.supabase_client import SupabaseClient': 
        'from vigia_detect.db.supabase_client_refactored import SupabaseClientRefactored as SupabaseClient',
    
    'from vigia_detect.messaging.twilio_client import TwilioClient':
        'from vigia_detect.messaging.twilio_client_refactored import TwilioClientRefactored as TwilioClient',
    
    'from vigia_detect.messaging.slack_notifier import SlackNotifier':
        'from vigia_detect.messaging.slack_notifier_refactored import SlackNotifierRefactored as SlackNotifier',
    
    # CLI
    'from vigia_detect.cli.process_images import':
        'from vigia_detect.cli.process_images_refactored import',
    
    # Validaciones
    'def validate_phone_number':
        '# Usar: from vigia_detect.utils.validators import validate_phone',
    
    'def validate_image':
        '# Usar: from vigia_detect.utils.validators import validate_image',
}

# Patrones de código a actualizar
CODE_PATTERNS = [
    # Variables de entorno hardcodeadas
    (r'os\.getenv\(["\']([A-Z_]+)["\']\s*,\s*["\'][^"\']+["\']\)',
     r'settings.\1.lower()'),
    
    # Tokens hardcodeados
    (r'["\']xoxb-\d+-\d+-[a-zA-Z0-9]+["\']',
     'settings.slack_bot_token'),
    
    # Logging básico
    (r'logging\.basicConfig\([^)]+\)',
     'logger = get_logger(__name__)'),
    
    # Crear modal historial duplicado
    (r'def crear_modal_historial[^(]*\([^)]*\):\s*"""[^"]*"""\s*return\s*{[^}]+}',
     'def crear_modal_historial():\n    return SlackModalTemplates.historial_medico()'),
]

# Archivos a excluir
EXCLUDE_PATTERNS = [
    '*_refactored.py',
    '__pycache__',
    '*.pyc',
    '.git',
    'tests',
    'migrations',
]


def should_process_file(file_path: Path) -> bool:
    """Determina si un archivo debe ser procesado"""
    # Excluir patrones
    for pattern in EXCLUDE_PATTERNS:
        if file_path.match(pattern):
            return False
    
    # Solo archivos Python
    return file_path.suffix == '.py'


def update_imports(content: str) -> Tuple[str, List[str]]:
    """Actualiza los imports en el contenido"""
    changes = []
    
    for old_import, new_import in IMPORT_MAPPINGS.items():
        if old_import in content:
            content = content.replace(old_import, new_import)
            changes.append(f"Import actualizado: {old_import}")
    
    return content, changes


def update_code_patterns(content: str) -> Tuple[str, List[str]]:
    """Actualiza patrones de código"""
    changes = []
    
    for pattern, replacement in CODE_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            changes.append(f"Patrón actualizado: {pattern[:30]}...")
    
    return content, changes


def add_required_imports(content: str) -> str:
    """Agrega imports necesarios si faltan"""
    imports_to_add = []
    
    # Si usa settings
    if 'settings.' in content and 'from config.settings import settings' not in content:
        imports_to_add.append('from config.settings import settings')
    
    # Si usa templates de Slack
    if 'SlackModalTemplates' in content and 'from vigia_detect.core.slack_templates' not in content:
        imports_to_add.append('from vigia_detect.core.slack_templates import SlackModalTemplates')
    
    # Si usa validadores
    if 'validate_phone' in content and 'from vigia_detect.utils.validators' not in content:
        imports_to_add.append('from vigia_detect.utils.validators import validate_phone')
    
    if imports_to_add:
        # Agregar después de los imports existentes
        import_section_end = 0
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_section_end = i + 1
        
        # Insertar nuevos imports
        for imp in imports_to_add:
            lines.insert(import_section_end, imp)
            import_section_end += 1
        
        content = '\n'.join(lines)
    
    return content


def process_file(file_path: Path, dry_run: bool = True) -> bool:
    """Procesa un archivo individual"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        all_changes = []
        
        # Actualizar imports
        content, import_changes = update_imports(content)
        all_changes.extend(import_changes)
        
        # Actualizar patrones de código
        content, code_changes = update_code_patterns(content)
        all_changes.extend(code_changes)
        
        # Agregar imports necesarios
        content = add_required_imports(content)
        
        # Si hubo cambios
        if content != original_content:
            print(f"\n📄 {file_path}")
            for change in all_changes:
                print(f"  ✓ {change}")
            
            if not dry_run:
                # Hacer backup
                backup_path = file_path.with_suffix('.py.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Escribir cambios
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"  💾 Archivo actualizado (backup en {backup_path})")
            else:
                print(f"  🔍 [DRY RUN] No se aplicaron cambios")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {e}")
        return False


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migra código al nuevo estilo refactorizado'
    )
    parser.add_argument(
        'path',
        type=str,
        help='Archivo o directorio a procesar'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Aplicar cambios (por defecto es dry-run)'
    )
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Procesar directorios recursivamente'
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    dry_run = not args.apply
    
    if dry_run:
        print("🔍 Modo DRY RUN - No se aplicarán cambios")
        print("   Usa --apply para aplicar los cambios\n")
    
    files_to_process = []
    
    if path.is_file():
        files_to_process.append(path)
    elif path.is_dir():
        if args.recursive:
            files_to_process.extend(
                p for p in path.rglob('*.py') 
                if should_process_file(p)
            )
        else:
            files_to_process.extend(
                p for p in path.glob('*.py')
                if should_process_file(p)
            )
    else:
        print(f"❌ Ruta no válida: {path}")
        return 1
    
    print(f"📋 Procesando {len(files_to_process)} archivos...\n")
    
    processed = 0
    for file_path in files_to_process:
        if process_file(file_path, dry_run):
            processed += 1
    
    print(f"\n✅ Procesados {processed}/{len(files_to_process)} archivos con cambios")
    
    if dry_run and processed > 0:
        print("\n💡 Ejecuta con --apply para aplicar los cambios")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())