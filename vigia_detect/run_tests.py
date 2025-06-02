#!/usr/bin/env python3
"""
Script para ejecutar todos los tests del sistema LPP-Detect.

Este script ejecuta los tests unitarios y de integración para todos
los componentes del sistema, utilizando pytest y la estructura modular.
"""

import os
import sys
import pytest
from pathlib import Path

def run_tests():
    """Ejecuta todos los tests del proyecto."""
    # Obtener directorio raíz del proyecto
    root_dir = Path(__file__).resolve().parent
    
    # Añadir directorio raíz al path para importaciones
    sys.path.append(str(root_dir))
    
    # Ejecutar pytest para todos los tests
    return pytest.main([
        '--verbose',
        '-xvs',
        '--import-mode=importlib',  # Modo de importación para evitar problemas con paths
        'cli/tests',
        'cv_pipeline/tests',
        'db/tests',
        'utils/tests'
    ])

if __name__ == "__main__":
    # Ejecutar tests
    status = run_tests()
    
    # Salir con código de estado apropiado
    sys.exit(status)
