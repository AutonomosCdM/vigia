# Gestión de Credenciales - Vigia

## 🔐 Sistema de Credenciales Seguras

Vigia incluye un sistema de gestión de credenciales que almacena las claves de forma segura en el keychain del sistema.

## 🚀 Configuración Inicial

### 1. Configurar credenciales por primera vez:

```bash
python scripts/setup_credentials.py
```

Este script:
- Almacena las credenciales en el keychain del sistema (seguro)
- Permite actualizar credenciales existentes
- Exporta a `.env.local` para desarrollo
- Genera archivo para Render deployment

### 2. Cargar credenciales en tu sesión:

```bash
source scripts/quick_env_setup.sh
```

## 📋 Credenciales Requeridas

1. **Twilio** (para WhatsApp):
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_FROM` (formato: whatsapp:+1234567890)

2. **Anthropic** (para IA):
   - `ANTHROPIC_API_KEY`

3. **Supabase** (base de datos):
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

## 🔄 Flujo de Trabajo

### Desarrollo Local:

1. Configurar credenciales una vez:
   ```bash
   python scripts/setup_credentials.py
   # Opción 1: Configurar credenciales
   # Opción 3: Exportar a .env.local
   ```

2. En cada sesión de desarrollo:
   ```bash
   source scripts/quick_env_setup.sh
   ```

### Deployment a Render:

1. Generar archivo con credenciales:
   ```bash
   python scripts/setup_credentials.py
   # Opción 4: Generar archivo para Render
   ```

2. Copiar contenido de `render_env.txt` a Render

## 🔒 Seguridad

- Las credenciales se almacenan en el keychain del sistema (encriptadas)
- `.env.local` está en `.gitignore` (nunca se sube a Git)
- No hardcodear credenciales en el código
- Usar siempre variables de entorno

## 🛠️ Solución de Problemas

### "No se encontró .env.local"
```bash
python scripts/setup_credentials.py
# Opción 3: Exportar a .env.local
```

### "Credencial no configurada"
```bash
python scripts/setup_credentials.py
# Opción 1: Configurar credenciales
```

### Ver credenciales configuradas
```bash
python scripts/setup_credentials.py
# Opción 2: Ver credenciales configuradas
```

## 📝 Notas

- Las credenciales se almacenan de forma segura y persistente
- No necesitas ingresarlas cada vez que trabajas en el proyecto
- El sistema funciona en macOS (Keychain), Linux (Secret Service), y Windows (Windows Credential Vault)