# 🏥 DIAGRAMA DE FLUJO - SISTEMA VIGÍA
## Flujo Completo: WhatsApp → Detección → Slack → Respuesta

---

## 🔄 FLUJO PRINCIPAL DE DATOS

```mermaid
graph TD
    %% Entrada del paciente/enfermera
    A[👩‍⚕️ Enfermera/Cuidador] -->|Envía foto + código paciente| B[📱 WhatsApp]
    
    %% Sistema de mensajería WhatsApp
    B --> C[🌐 Twilio Webhook]
    C --> D[🔍 WhatsApp Processor]
    D --> E{📋 ¿Imagen válida?}
    
    %% Validación inicial
    E -->|❌ No| F[⚠️ Error: Imagen inválida]
    E -->|✅ Sí| G[💾 Guardar imagen temporal]
    F --> H[📱 Respuesta WhatsApp Error]
    
    %% Pipeline de detección
    G --> I[🤖 Sistema de Detección]
    I --> J[🔬 Preprocessor]
    J --> K[🎯 YOLO Detector]
    K --> L[🧠 Claude AI Analysis]
    
    %% Procesamiento de resultados
    L --> M{🩺 ¿LPP Detectada?}
    M -->|❌ No LPP| N[✅ Resultado Negativo]
    M -->|🔍 LPP Detectada| O[⚠️ Clasificación Grado 1-4]
    
    %% Almacenamiento y notificaciones
    N --> P[💾 Supabase DB]
    O --> P
    P --> Q[📊 Redis Cache Update]
    Q --> R[🔔 Slack Notification]
    
    %% Sistema Slack
    R --> S[👥 Canal Médico Slack]
    S --> T[🩺 Equipo Médico]
    T --> U{⚕️ ¿Acción requerida?}
    
    %% Acciones del equipo médico
    U -->|📋 Ver Historial| V[📖 Modal Historial Paciente]
    U -->|🏥 Solicitar Evaluación| W[🚨 Alerta Evaluación Médica]
    U -->|✅ Marcar Resuelto| X[✔️ Caso Cerrado]
    U -->|📞 Contactar Enfermera| Y[📱 Respuesta WhatsApp]
    
    %% Respuestas y follow-up
    V --> Z[📊 Dashboard Grafana]
    W --> AA[📧 Notificación Urgente]
    X --> BB[📈 Métricas Actualizadas]
    Y --> CC[👩‍⚕️ Enfermera recibe instrucciones]
    
    %% Webhook externo (opcional)
    P --> DD[🔗 Webhook Externo]
    DD --> EE[🏥 Sistema Hospitalario]

    %% Estilos
    classDef user fill:#e1f5fe
    classDef whatsapp fill:#25d366,color:#fff
    classDef detection fill:#ff9800,color:#fff
    classDef slack fill:#4a154b,color:#fff
    classDef database fill:#1976d2,color:#fff
    classDef medical fill:#d32f2f,color:#fff
    
    class A user
    class B,H,Y,CC whatsapp
    class I,J,K,L,M,N,O detection
    class R,S,T,U,V,W,X slack
    class P,Q,DD,EE database
    class T,V,W,X,AA medical
```

---

## 🔍 DETALLE DE COMPONENTES

### 📱 **1. ENTRADA WHATSAPP**
```
Flujo: Enfermera → WhatsApp → Twilio → Vigia
├── 📸 Imagen LPP (JPG/PNG)
├── 🏷️ Código Paciente (CD-2025-001)
├── 📝 Mensaje opcional
└── 🔐 Validación formato
```

### 🤖 **2. PIPELINE DE DETECCIÓN**
```
vigia_detect/cv_pipeline/
├── 🔍 Preprocessor
│   ├── Redimensionamiento imagen
│   ├── Normalización colores
│   └── Limpieza de ruido
├── 🎯 YOLO Detector
│   ├── Detección objeto LPP
│   ├── Bounding boxes
│   └── Confidence scores
└── 🧠 Claude AI Analysis
    ├── Clasificación grado LPP (0-4)
    ├── Análisis contexto médico
    └── Recomendaciones protocolo
```

### 💾 **3. ALMACENAMIENTO**
```
Supabase Database:
├── 👤 patients (datos anonimizados)
├── 🔍 detections (resultados IA)
├── 📸 images (metadata + URLs)
├── 📊 medical_protocols (cache)
└── 🔒 audit_logs (trazabilidad)

Redis Cache:
├── 🏥 Medical protocols
├── 📈 Patient history
└── ⚡ Fast lookups
```

### 🔔 **4. NOTIFICACIÓN SLACK**
```
vigia_detect/messaging/slack_notifier_refactored.py
├── 📋 Bloque Header (Paciente + Grado)
├── 📊 Campos Detalle (Confianza + Ubicación)
├── 📸 Imagen Adjunta (si configurado)
├── 🔘 Botones Acción
│   ├── 📖 Ver Historial Médico
│   ├── 🏥 Solicitar Evaluación
│   └── ✅ Marcar Resuelto
└── 📝 Contexto Sistema
```

### ⚕️ **5. ACCIONES MÉDICAS**
```
Slack Interactions:
├── 📋 Modal Historial
│   ├── Diagnósticos actuales
│   ├── Medicación activa  
│   ├── Historial LPP previo
│   └── Observaciones enfermería
├── 🚨 Alerta Evaluación
│   ├── Notificación urgente
│   ├── Escalamiento automático
│   └── Timer de respuesta
└── ✅ Resolución Caso
    ├── Tiempo resolución
    ├── Acciones tomadas
    └── Actualización métricas
```

---

## 📊 FLUJO DE DATOS TÉCNICO

### 🔄 **Estados del Sistema**
```python
# Estado de procesamiento
ProcessingStates = {
    'RECEIVED': 'Imagen recibida vía WhatsApp',
    'VALIDATING': 'Validando formato y calidad',
    'PROCESSING': 'Ejecutando detección IA',
    'ANALYZING': 'Análisis médico con Claude',
    'STORING': 'Guardando en base de datos',
    'NOTIFYING': 'Enviando notificación Slack',
    'COMPLETED': 'Proceso completado exitosamente',
    'FAILED': 'Error en procesamiento'
}
```

### 🚨 **Alertas y Escalamiento**
```python
# Niveles de urgencia
UrgencyLevels = {
    'GRADE_0': {'color': 'good', 'urgency': 'BAJA'},
    'GRADE_1': {'color': 'warning', 'urgency': 'MEDIA'},
    'GRADE_2': {'color': 'warning', 'urgency': 'IMPORTANTE'},
    'GRADE_3': {'color': 'danger', 'urgency': 'ALTA'},
    'GRADE_4': {'color': 'danger', 'urgency': 'CRÍTICA'}
}
```

---

## 🔗 INTEGRACIONES EXTERNAS

### 📡 **Webhooks Sistema Hospitalario**
```mermaid
graph LR
    A[💾 Supabase] -->|POST| B[🔗 Webhook Client]
    B -->|JSON Payload| C[🏥 Hospital System]
    C -->|Response| D[📊 Acknowledgment]
    D --> E[📈 Metrics Update]
    
    style A fill:#1976d2,color:#fff
    style B fill:#ff9800,color:#fff
    style C fill:#4caf50,color:#fff
```

### 📊 **Monitoreo en Tiempo Real**
```
Grafana Dashboards:
├── 🩺 Medical Dashboard
│   ├── Casos activos por grado
│   ├── Tiempo promedio respuesta
│   ├── Eficacia detección IA
│   └── Distribución por servicio
├── 🔧 Technical Dashboard
│   ├── Performance del pipeline
│   ├── Errores y excepciones
│   ├── Uso de recursos
│   └── Latencia de componentes
└── 🔒 Security Dashboard
    ├── Intentos acceso no autorizado
    ├── Anomalías en el sistema
    └── Cumplimiento HIPAA
```

---

## ⏱️ TIEMPOS DE RESPUESTA

### 📈 **SLA del Sistema**
```
Proceso Completo: WhatsApp → Slack
├── 📱 Recepción WhatsApp: <2 segundos
├── 🔍 Validación imagen: <1 segundo
├── 🤖 Detección IA: <10 segundos
├── 🧠 Análisis Claude: <5 segundos
├── 💾 Almacenamiento: <2 segundos
├── 🔔 Notificación Slack: <3 segundos
└── 📊 Total Target: <25 segundos
```

### 🎯 **Métricas de Calidad**
```
KPIs Principales:
├── 🎯 Precisión Detección: >95%
├── ⚡ Tiempo Respuesta: <25s
├── 🔄 Disponibilidad: 99.9%
├── 📊 Satisfacción Usuario: >4.5/5
└── 🔒 Incidentes Seguridad: 0
```

---

## 🔒 SEGURIDAD Y COMPLIANCE

### 🛡️ **Controles de Seguridad**
```
Puntos de Control:
├── 🔐 WhatsApp: Encriptación E2E
├── 🔒 Twilio: HTTPS + Auth tokens
├── 🛡️ Vigia API: JWT + Rate limiting
├── 💾 Supabase: RLS + Encryption
├── 🔗 Slack: Bearer tokens + Signing
└── 📊 Grafana: RBAC + Audit logs
```

### 📋 **Trazabilidad HIPAA**
```python
# Cada transacción genera audit log
AuditLog = {
    'timestamp': 'ISO datetime',
    'user_id': 'ID usuario (anonimizado)',
    'patient_code': 'Código paciente',
    'action': 'DETECTION_PROCESSED',
    'details': 'Metadata sin PII',
    'ip_address': 'IP hash (no original)',
    'session_id': 'Session tracking'
}
```

---

## 🚀 DESPLIEGUE Y ESCALABILIDAD

### 🐳 **Arquitectura de Contenedores**
```
Docker Compose Services:
├── 🤖 vigia-api (FastAPI)
├── 📱 whatsapp-processor (Twilio webhook)
├── 🔔 slack-notifier (Slack integration)
├── 💾 redis-cache (Medical protocols)
├── 📊 grafana (Monitoring)
└── 🔍 prometheus (Metrics collection)
```

### ⚡ **Auto-scaling**
```
Scaling Triggers:
├── CPU > 70% → Scale out detection pods
├── Memory > 80% → Increase Redis cache
├── Queue depth > 50 → Add worker processes
└── Error rate > 1% → Alert + failover
```

---

<div align="center">

## 🏥 RESUMEN EJECUTIVO

**El Sistema Vigía proporciona un flujo completo automatizado para la detección y gestión de lesiones por presión, integrando WhatsApp, IA de detección, y notificaciones Slack en un pipeline médico seguro y conforme a HIPAA.**

### 📊 Flujo Resumido:
**📱 WhatsApp → 🤖 IA Detección → 💾 Database → 🔔 Slack → ⚕️ Acción Médica**

---

*Diagrama generado para Certificación Técnica CERT-VIGIA-2025-001*

</div>