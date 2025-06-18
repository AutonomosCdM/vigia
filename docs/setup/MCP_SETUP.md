# MCP (Model Context Protocol) Setup for Vigia

## 📋 MCPs Configurados

Los siguientes MCPs están configurados para el proyecto Vigia:

### 1. **Slack MCP**
- **Propósito**: Enviar mensajes a canales de Slack
- **Canal**: #it_vigia (C08U2TB78E6)
- **Configuración**: Bot token y team ID configurados

### 2. **GitHub MCP**
- **Propósito**: Interactuar con repositorios GitHub
- **Repositorio**: AutonomosCdM/pressure
- **Funciones**: Issues, PRs, commits, releases

### 3. **Filesystem MCP**
- **Propósito**: Acceso a archivos del proyecto
- **Directorio**: /Users/autonomos_dev/Projects/vigia
- **Permisos**: Lectura/escritura en directorio del proyecto

### 4. **Brave Search MCP**
- **Propósito**: Búsquedas web para documentación e investigación
- **Estado**: Activo

## 🔧 Configuración Actual

### Archivo .mcp.json
```json
{
  "mcpServers": {
    "slack": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-***",
        "SLACK_TEAM_ID": "T084BMT9H4N",
        "SLACK_CHANNEL_IDS": "C08U2TB78E6"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "github_pat_***"
      }
    },
    "filesystem": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "ALLOWED_DIRECTORIES": "/Users/autonomos_dev/Projects/vigia"
      }
    }
  }
}
```

## 🚀 Comandos de Gestión

### Listar MCPs
```bash
claude mcp list
```

### Añadir MCP
```bash
claude mcp add -s project <name> <command> [args...]
```

### Remover MCP
```bash
claude mcp remove <name>
```

### Verificar Estado
```bash
/mcp  # En Claude Code
```

## 📝 Uso de Slack MCP

Para enviar el resumen del proyecto v1.3.3 al canal #it_vigia:

1. Los MCPs deben estar activos
2. Claude Code debe tener acceso a las herramientas MCP
3. El bot debe estar invitado al canal #it_vigia

### Mensaje de Ejemplo
```
🚀 Vigía v1.3.3 - Redis Phase 2 Completado!
- 92% precisión en búsqueda semántica
- 4 protocolos médicos indexados
- Caché contextual por paciente
```

## 🔒 Seguridad

- Los tokens están en archivos locales (.env y .mcp.json)
- NO commitear tokens al repositorio
- Los MCPs de proyecto requieren aprobación
- Permisos limitados por directorio

## 🛠️ Troubleshooting

### MCPs no aparecen
1. Verificar .mcp.json existe
2. Revisar sintaxis JSON
3. Confirmar tokens válidos
4. Reiniciar Claude Code

### Slack no funciona
1. Verificar bot está en canal
2. Confirmar permisos del bot
3. Validar SLACK_BOT_TOKEN
4. Comprobar SLACK_TEAM_ID

### GitHub no responde
1. Validar GITHUB_PERSONAL_ACCESS_TOKEN
2. Confirmar permisos del token
3. Verificar conectividad

## 📅 Mantenimiento

- **Tokens Slack**: Rotar cada 90 días
- **GitHub PAT**: Verificar expiración
- **MCPs**: Actualizar paquetes NPM mensualmente

---

**Última actualización**: Mayo 2025
**Configurado por**: Claude Code Assistant