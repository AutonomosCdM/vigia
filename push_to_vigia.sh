#!/bin/bash
# Script para subir el código al nuevo repositorio vigia

echo "Preparando para subir al repositorio vigia..."

# Verificar que estamos en el directorio correcto
if [ ! -d ".git" ]; then
    echo "Error: No estás en un repositorio git"
    exit 1
fi

# Mostrar el estado actual
echo "Estado actual del repositorio:"
git status

# Confirmar con el usuario
read -p "¿Deseas continuar y subir al repositorio vigia? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Operación cancelada"
    exit 1
fi

# Subir al nuevo repositorio
echo "Subiendo al repositorio vigia..."
git push -u origin main

echo "✅ Código subido exitosamente al repositorio vigia!"
echo "🔗 URL: https://github.com/AutonomosCdM/vigia"