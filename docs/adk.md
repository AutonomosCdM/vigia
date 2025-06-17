ANÁLISIS Y MIGRACIÓN COMPLETA LPP-DETECT A ADK/A2A

## CONTEXTO Y OBJETIVO

Eres un arquitecto de software experto en Google Agent Development Kit (ADK) y el protocolo Agent-to-Agent (A2A). Tu misión es analizar exhaustivamente el proyecto LPP-Detect (sistema de detección de lesiones por presión) y crear un plan de migración detallado para transformarlo en una implementación 100% compatible con ADK y A2A para el Google Cloud Multi-Agent Hackathon.

## INFORMACIÓN DEL PROYECTO ACTUAL

**LPP-Detect (Vigía System)** es un sistema de salud que:
- Detecta lesiones por presión usando WhatsApp → Procesamiento IA → Notificación Slack → Personal médico
- Tiene 5 agentes conceptuales: ImageAnalysisAgent, ClinicalAssessmentAgent, ProtocolAgent, CommunicationAgent, WorkflowOrchestrationAgent
- Usa Celery + Redis para orquestación asíncrona
- Implementa HIPAA compliance con PHI tokenization
- Usa Bio-LLaMA 2.7B, YOLOv5, MONAI para procesamiento médico
- Base de datos Supabase con esquema FHIR temporal
- Desplegado en Hospital Quilpué, Chile

## TAREAS ESPECÍFICAS A REALIZAR

### 1. ANÁLISIS COMPLETO DEL CÓDIGO ACTUAL
- Examina TODA la estructura de directorios del proyecto
- Identifica cada archivo Python, configuración, y dependencia
- Mapea el flujo de datos actual desde WhatsApp hasta la respuesta final
- Documenta todas las integraciones externas (APIs, servicios, bases de datos)
- Lista todos los modelos de IA/ML utilizados y sus propósitos
- Identifica patrones de código que necesitan refactoring para ADK

### 2. EVALUACIÓN DE CUMPLIMIENTO ADK
Para cada componente del sistema actual, evalúa:
- ¿Cumple con la arquitectura de agentes ADK (BaseAgent, LlmAgent, WorkflowAgent)?
- ¿Usa el patrón parent-child con sub_agents correctamente?
- ¿Implementa InvocationContext y state sharing via output_key?
- ¿Soporta los tres tipos de workflow: Sequential, Parallel, Loop?
- ¿Permite LLM-driven delegation con transfer_to_agent?
- ¿Está preparado para streaming bidireccional?
- ¿Usa las herramientas (Tools) de ADK correctamente?
- ¿Implementa callbacks para cross-cutting concerns?

### 3. EVALUACIÓN DE CUMPLIMIENTO A2A
Verifica si el sistema actual tiene:
- Agent Cards en formato JSON para capability discovery
- Comunicación via JSON-RPC 2.0 sobre HTTPS
- Implementación del concepto "Task" con lifecycle completo
- Soporte para los tres modos: Request/Response, Streaming (SSE), Push notifications
- Autenticación estandarizada (OAuth 2.0, API keys)
- Separación clara entre Remote Agents, Clients, y Users
- Capacidad de publicar y consumir Agent Cards de otros sistemas

### 4. PLAN DE MIGRACIÓN DETALLADO (solo en modo plan, no hacer cambios aún)

#### 4.1 Arquitectura Target ADK
Diseña la nueva arquitectura con:
- **Root Agent** (orquestador principal) con jerarquía clara
- **Sub-agents especializados** con responsabilidades definidas
- **Tools** para cada capacidad (análisis imagen, consulta DB, etc.)
- **State management** usando InvocationContext
- **Workflow patterns** apropiados (Sequential para pipeline médico)
- **Callbacks** para seguridad y compliance HIPAA

Proporciona código Python completo para cada agente.

#### 4.2 Implementación A2A
Para cada agente, crea:
- **Agent Card JSON** completo con capabilities, authentication, endpoints
- **Servidor A2A** con métodos JSON-RPC
- **Cliente A2A** para consumir otros agentes
- **Task management** con estados y artifacts
- **Authentication flow** con OAuth 2.0

Proporciona ejemplos de código para servidores y clientes.

#### 4.3 Integración Google Cloud (Bonus Points)
Planifica migración a:
- **Gemini 2.0** en lugar de Bio-LLaMA (via Vertex AI) Analizar PalmMed2 o MedGemma. 
- **Cloud Run** para deployment de agentes
- **Firestore/BigQuery** en lugar de Supabase
- **Cloud Healthcare API** para compliance FHIR
- **Vertex AI Agent Engine** para orquestación
- **Cloud Storage** para imágenes médicas
- **Identity Platform** para autenticación

#### 4.4 Plan de Migración Incremental
Crea un plan que:
- **NO rompa** el sistema en producción en el hospital, puede ser un nuevo repo
- Use **wrapper pattern** para migración gradual
- Mantenga **compliance médico** en todo momento
- Permita **rollback** si hay problemas
- Incluya **tests** para cada componente migrado

### 5. CÓDIGO DE MIGRACIÓN

Proporciona código Python COMPLETO para:

#### 5.1 Estructura ADK Base
```python
# Ejemplo de estructura esperada
from google.adk.agents import LlmAgent, SequentialAgent, BaseAgent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService

class MedicalImageAnalysisAgent(LlmAgent):
    # Implementación completa
    pass

class ClinicalRiskAssessmentAgent(LlmAgent):
    # Implementación completa
    pass

# etc...
```

#### 5.2 Servidor A2A
```python
# Ejemplo de implementación A2A
from google.a2a import A2AServer, AgentCard, Task

class ImageAnalysisA2AServer(A2AServer):
    def get_agent_card(self) -> AgentCard:
        # Implementación completa
        pass
    
    def process_task(self, task: Task) -> dict:
        # Implementación completa
        pass
```

#### 5.3 Wrappers de Migración
```python
# Código para mantener compatibilidad durante migración
class CeleryToADKWrapper:
    # Permite que código viejo funcione con nueva arquitectura
    pass
```

### 6. TESTING Y VALIDACIÓN

Crea:
- Suite de tests unitarios para cada agente ADK
- Tests de integración para flujo A2A completo
- Tests de compliance médico (HIPAA, MINSAL)
- Tests de performance y escalabilidad
- Validación de Agent Cards y JSON-RPC

### 7. DOCUMENTACIÓN Y CONTENIDO

Prepara:
- README.md actualizado con arquitectura ADK/A2A
- Diagramas de flujo y secuencia
- Guía de deployment en Google Cloud
- Blog post técnico (para bonus points)
- Video demo del sistema funcionando

### 8. CONTRIBUCIONES ADK (BONUS)

Identifica oportunidades para:
- PRs al repositorio ADK con herramientas médicas
- Issues sobre casos de uso healthcare
- Ejemplos de código para la comunidad
- Mejoras a la documentación

## FORMATO DE ENTREGA

Tu respuesta debe incluir:

1. **ANÁLISIS ACTUAL** (2-3 páginas)
   - Estructura de directorios completa
   - Flujo de datos actual
   - Gaps vs ADK/A2A

2. **ARQUITECTURA TARGET** (3-4 páginas)
   - Diagramas UML/arquitectura
   - Descripción de cada agente
   - Flujos de comunicación A2A

3. **CÓDIGO COMPLETO** (10-15 páginas)
   - Todos los agentes ADK
   - Servidores A2A
   - Agent Cards JSON
   - Wrappers de migración

4. **PLAN DE MIGRACIÓN** (2-3 páginas)
   - Timeline semana por semana
   - Riesgos y mitigaciones
   - Checklist de validación

5. **EXTRAS PARA BONUS** (1-2 páginas)
   - Integración Google Cloud
   - Plan de contenido
   - PRs propuestos

## CONSIDERACIONES ESPECIALES

- **Prioridad 1**: Mantener funcionamiento en hospital durante migración
- **Prioridad 2**: Cumplir 100% con ADK hierarchy y state management
- **Prioridad 3**: Implementar A2A protocol completamente
- **Prioridad 4**: Maximizar bonus points con Google Cloud y contenido

## RESTRICCIONES

- Mantener compliance HIPAA y normativas chilenas MINSAL
- Código debe ser production-ready, no prototipos
- Documentación debe ser clara para jueces del hackathon

https://googlecloudmultiagents.devpost.com/resources
https://github.com/GoogleCloudPlatform
https://github.com/google/adk-samples
https://github.com/google-a2a/A2A
https://google-a2a.github.io/A2A/latest/#a2a-and-mcp-complementary-protocols
https://google-a2a.github.io/A2A/specification/#2-core-concepts-summary
---

**IMPORTANTE**: Analiza CADA archivo del proyecto actual. No asumas nada. Proporciona código FUNCIONAL completo, no pseudocódigo. El objetivo es ganar el hackathon con la mejor implementación ADK/A2A en healthcare.