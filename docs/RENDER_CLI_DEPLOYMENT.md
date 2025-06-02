# Deployment con Render CLI - Guía Completa

## 🚀 Configuración Inicial

### 1. Instalar Render CLI

```bash
# macOS con Homebrew
brew install render

# Linux/macOS alternativo
curl -fsSL https://raw.githubusercontent.com/render-oss/cli/refs/heads/main/bin/install.sh | sh
```

### 2. Autenticación

```bash
# Login interactivo
render login

# Verificar autenticación
render whoami
```

### 3. Obtener API Key

1. Ve a: https://dashboard.render.com/u/settings#api-keys
2. Crea un nuevo API key
3. Guárdalo de forma segura:

```bash
# Agregar a tu .bashrc o .zshrc
export RENDER_API_KEY='rnd_XXXXXXXXXXXXXXXXXXXXXXXXXX'
```

## 📋 Comandos Básicos del CLI

### Listar Servicios
```bash
# Modo interactivo
render services

# Modo JSON (para scripts)
render services --output json
```

### Ver Logs
```bash
# Logs en tiempo real
render logs [SERVICE_ID] --tail

# Últimas 100 líneas
render logs [SERVICE_ID] --lines 100
```

### Crear Deploys
```bash
# Deploy manual
render deploys create [SERVICE_ID]

# Deploy de commit específico
render deploys create [SERVICE_ID] --commit [SHA]
```

### SSH a Servicios
```bash
render ssh [SERVICE_ID]
```

## 🔧 Deployment Automatizado

### Script Principal: `deploy_with_render.sh`

Este script automatiza todo el proceso de deployment:

```bash
# Uso básico
./scripts/deploy_with_render.sh

# Opciones disponibles:
# 1) Deploy todos los servicios
# 2) Deploy un servicio específico
# 3) Ver logs de servicios
# 4) Verificar estado de servicios
# 5) Conectar Environment Groups
```

### Conectar Environment Groups

El script `connect_env_groups.py` automatiza la conexión de variables de entorno:

```bash
# Asegurarse de tener RENDER_API_KEY configurado
export RENDER_API_KEY='tu-api-key'

# Ejecutar
python scripts/connect_env_groups.py
```

## 🔄 Workflow de Deployment

### 1. Desarrollo Local
```bash
# Hacer cambios
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main
```

### 2. Deploy Automático
```bash
# Opción 1: Deploy todos los servicios
./scripts/deploy_with_render.sh
# Seleccionar opción 1

# Opción 2: Deploy específico
./scripts/deploy_with_render.sh
# Seleccionar opción 2 y elegir servicio
```

### 3. Monitoreo
```bash
# Ver logs en tiempo real
./scripts/deploy_with_render.sh
# Seleccionar opción 3

# Verificar estado
./scripts/deploy_with_render.sh
# Seleccionar opción 4
```

## 📊 Estructura del Proyecto en Render

```
vigia (Environment Group)
├── vigia-whatsapp (Web Service)
├── vigia-webhook (Web Service)
├── vigia-worker (Background Worker)
└── vigia-redis (Redis)
```

## 🔐 Variables de Entorno

Las variables están centralizadas en el Environment Group "vigia":

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM`
- `ANTHROPIC_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`

## 🛠️ Solución de Problemas

### Error: "CLI no autenticado"
```bash
render login
```

### Error: "Service not found"
```bash
# Verificar servicios disponibles
render services --output json | jq '.[] | .service.name'
```

### Error: "Environment variables missing"
```bash
# Reconectar environment groups
python scripts/connect_env_groups.py
```

## 📝 Notas Importantes

1. **Limitaciones del CLI**: El CLI de Render no soporta nativamente environment groups, por eso usamos la API REST
2. **API Key**: Mantén tu API key segura, no la commitees al repositorio
3. **Deployments**: Los deploys automáticos se activan con cada push a `main`
4. **Logs**: Los logs se pueden ver tanto en el CLI como en el dashboard

## 🚨 Comandos de Emergencia

```bash
# Reiniciar un servicio
curl -X POST -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/[SERVICE_ID]/restart"

# Suspender un servicio
curl -X POST -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/[SERVICE_ID]/suspend"

# Reanudar un servicio
curl -X POST -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/[SERVICE_ID]/resume"
```

## 📚 Referencias

- [Documentación oficial del CLI](https://render.com/docs/cli)
- [API Reference](https://api-docs.render.com/reference/introduction)
- [Render Dashboard](https://dashboard.render.com)