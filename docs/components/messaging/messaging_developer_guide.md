# LPP-Detect Messaging Developer Guide

Este documento proporciona una guía detallada para desarrolladores que trabajan con el módulo de messaging de LPP-Detect.

## Architecture Overview

El módulo de messaging facilita la comunicación bidireccional entre el sistema LPP-Detect y los usuarios a través de WhatsApp, utilizando la plataforma Twilio. La arquitectura está diseñada para ser modular, escalable y segura, manejando tanto mensajes de texto como contenido multimedia (imágenes).

```mermaid
graph TD
    A[Usuario WhatsApp] --> B{Twilio WhatsApp API};
    B --> C[Twilio Webhook];
    C --> D[WhatsApp Server (Flask)];
    D --> E[WhatsApp Processor];
    E --> F[CV Pipeline];
    E --> G[ADK Agents];
    E --> H[Database Module];
    E --> I[Slack Integration];
    F --> E;
    G --> E;
    H --> E;
    I --> E;
    E --> J[TwilioClient];
    J --> B;
    B --> A;

    subgraph Messaging Module
        D; E; J;
    end

    subgraph External Services
        A; B; C; I;
    end

    subgraph LPP-Detect Core
        F; G; H;
    end

    style Messaging Module fill:#f9f,stroke:#333,stroke-width:2px
    style External Services fill:#ccf,stroke:#333,stroke-width:2px
    style LPP-Detect Core fill:#cfc,stroke:#333,stroke-width:2px
```

**Flujo de Comunicación (WhatsApp → Sistema → Slack → Sistema → WhatsApp):**

1.  **Mensaje Entrante:** Un usuario envía un mensaje (texto o imagen) a través de WhatsApp.
2.  **Twilio API:** Twilio recibe el mensaje y lo envía como una solicitud POST (webhook) al endpoint configurado en el `WhatsApp Server`.
3.  **WhatsApp Server:** El servidor recibe la solicitud, valida su origen (firma de Twilio) y extrae los datos relevantes.
4.  **WhatsApp Processor:** El procesador toma los datos del webhook. Si hay imágenes, las descarga de forma segura.
5.  **Integración con Core:** El procesador interactúa con el `CV Pipeline` para analizar las imágenes, con los `ADK Agents` para lógica de negocio (triage, interpretación) y con el `Database Module` para persistir datos.
6.  **Notificación a Slack:** Los `ADK Agents` o el procesador pueden enviar notificaciones relevantes al canal de Slack a través de la integración correspondiente.
7.  **Generación de Respuesta:** Basado en los resultados del análisis y la lógica de negocio, el procesador determina la respuesta adecuada para el usuario. Esto puede ser un mensaje de texto simple o una plantilla estructurada.
8.  **TwilioClient:** El procesador utiliza el `TwilioClient` para enviar la respuesta generada de vuelta a la API de Twilio.
9.  **Twilio API:** Twilio envía el mensaje de respuesta al usuario en WhatsApp.

## Development Setup

1.  Asegúrate de tener Python 3.7+ instalado.
2.  Clona el repositorio LPP-Detect.
3.  Instala las dependencias del proyecto (`pip install -r requirements.txt`).
4.  Configura las variables de entorno de Twilio (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`) en un archivo `.env` en la raíz del proyecto.
5.  Para recibir webhooks de Twilio en tu entorno de desarrollo local, necesitarás exponer tu servidor local a internet. Herramientas como `ngrok` son útiles para esto (`ngrok http 5005`). Configura la URL pública proporcionada por `ngrok` como la URL de webhook en la configuración de tu número de WhatsApp en la consola de Twilio.

## Common Workflows

### Procesamiento de Imagen con Análisis CV

1.  Usuario envía imagen por WhatsApp.
2.  Webhook llega al `WhatsApp Server`.
3.  `WhatsApp Server` valida y pasa datos al `WhatsApp Processor`.
4.  `WhatsApp Processor` descarga la imagen a `whatsapp/temp/`.
5.  `WhatsApp Processor` envía la ruta de la imagen al `CV Pipeline`.
6.  `CV Pipeline` realiza el análisis y devuelve los resultados al `WhatsApp Processor`.
7.  `WhatsApp Processor` utiliza `ADK Agents` para interpretar los resultados y determinar la gravedad de la LPP.
8.  `WhatsApp Processor` selecciona la plantilla de mensaje adecuada (`templates/whatsapp_templates.py`) basada en la gravedad.
9.  `WhatsApp Processor` formatea los parámetros de la plantilla.
10. `WhatsApp Processor` utiliza `TwilioClient.send_whatsapp_template` para enviar la respuesta al usuario.
11. Opcionalmente, `WhatsApp Processor` o un `ADK Agent` envía una notificación a Slack con un resumen del caso.
12. La información de la interacción y el resultado se guarda en la base de datos (`Database Module`).
13. La imagen temporal se elimina de `whatsapp/temp/` (implementar lógica de limpieza).

### Respuesta a Mensaje de Texto

1.  Usuario envía mensaje de texto por WhatsApp.
2.  Webhook llega al `WhatsApp Server`.
3.  `WhatsApp Server` valida y pasa datos al `WhatsApp Processor`.
4.  `WhatsApp Processor` identifica que es un mensaje de texto.
5.  `WhatsApp Processor` utiliza `ADK Agents` para procesar el texto (ej: responder preguntas frecuentes, iniciar un flujo).
6.  `WhatsApp Processor` utiliza `TwilioClient.send_whatsapp` para enviar la respuesta de texto al usuario.
7.  La interacción se registra en la base de datos.

## Testing

-   **Pruebas Unitarias:** Escribir pruebas para componentes individuales como `TwilioClient` (mockeando las llamadas a la API de Twilio), funciones de utilidad en `utils/twilio_utils.py`, y la lógica interna del `WhatsApp Processor` (mockeando las interacciones con CV, ADK, DB).
-   **Pruebas de Integración:** Probar el flujo completo desde la recepción de un webhook simulado hasta el envío de una respuesta (mockeando solo la llamada final a la API externa de Twilio). Utilizar herramientas como `pytest` y `vcrpy` para grabar y reproducir interacciones con la API de Twilio.
-   **Simulación de Webhooks:** Crear scripts o usar herramientas (como Postman o `curl`) para enviar solicitudes POST al endpoint `/webhook` del servidor local, simulando diferentes escenarios de mensajes entrantes (texto, imagen, con/sin media, etc.).
-   **Pruebas de Seguridad:** Verificar la validación de la firma de Twilio, el manejo seguro de archivos temporales y la protección de datos sensibles.

## Extending the Module

-   **Añadir Nuevos Canales de Mensajería:** La arquitectura modular permite integrar otros canales (ej: SMS, Facebook Messenger) creando nuevos clientes (similares a `TwilioClient`) y procesadores/servidores específicos para cada plataforma, manteniendo la lógica de negocio centralizada en el `WhatsApp Processor` o en agentes ADK.
-   **Añadir Nuevas Plantillas:** Definir nuevas plantillas en `templates/whatsapp_templates.py` y asegurarse de que el `WhatsApp Processor` pueda seleccionarlas y formatear sus parámetros correctamente.
-   **Mejorar el Procesamiento de Media:** Implementar manejo de otros tipos de media, validación más estricta de archivos, o integración con servicios de almacenamiento en la nube para las imágenes.
-   **Añadir Lógica de Negocio:** Extender la funcionalidad del `WhatsApp Processor` o crear nuevos `ADK Agents` para manejar nuevos tipos de mensajes, comandos de usuario, o flujos de interacción.

## Troubleshooting

-   **Webhooks no llegan:**
    -   Verificar que el servidor Flask esté corriendo y escuchando en el puerto correcto.
    -   Asegurarse de que la URL pública configurada en Twilio sea correcta y apunte a tu servidor local (si usas ngrok, verifica que esté activo).
    -   Revisar los logs de Twilio para ver si hay errores en la entrega del webhook.
    -   Verificar la configuración del firewall local.
-   **Errores al enviar mensajes:**
    -   Verificar que las variables de entorno de Twilio estén configuradas correctamente.
    -   Asegurarse de que el número de destino esté en formato E.164.
    -   Si usas plantillas, verificar que el `template_sid` sea correcto y que los parámetros proporcionados coincidan con los esperados por la plantilla.
    -   Revisar los logs de error de la API de Twilio en la consola de Twilio.
-   **Problemas con el procesamiento de imágenes:**
    -   Verificar que la URL de la media en los datos del webhook sea accesible.
    -   Asegurarse de que el directorio `whatsapp/temp/` tenga permisos de escritura.
    -   Revisar los logs del `WhatsApp Processor` y del `CV Pipeline` para errores durante la descarga o el análisis.
-   **Validación de firma de Twilio falla:**
    -   Asegurarse de que el `auth_token` utilizado para la validación sea el correcto.
    -   Verificar que el cuerpo de la solicitud y los encabezados se estén pasando correctamente a la función de validación.

## Best Practices

-   **Manejo Asíncrono:** Para operaciones que consumen tiempo (ej: análisis de imágenes, llamadas a APIs externas), considera implementar procesamiento asíncrono para evitar bloquear el servidor de webhooks y cumplir con los SLAs de respuesta de Twilio.
-   **Idempotencia:** Diseña los endpoints de webhook para ser idempotentes, de modo que recibir la misma solicitud varias veces no cause efectos secundarios no deseados.
-   **Logging:** Implementa logging detallado en todos los componentes para facilitar la depuración y el monitoreo.
-   **Manejo de Errores:** Implementa manejo robusto de errores y excepciones, registrando los errores y, si es posible, notificando al usuario o a los sistemas internos sobre el problema.
-   **Seguridad:** Siempre valida las solicitudes entrantes, sanea las entradas de usuario, y maneja la información sensible (PHI) con el máximo cuidado.
-   **Documentación:** Mantén esta guía y la referencia de la API actualizadas con cualquier cambio en el módulo.
-   **SLAs:** Ten en cuenta las restricciones de tiempo de Twilio para las respuestas a webhooks (generalmente 15 segundos). Las operaciones largas deben manejarse de forma asíncrona.
-   **Diseño UX:** Considera el diseño de la experiencia del usuario al redactar mensajes y definir los flujos de interacción para asegurar que la comunicación con el paciente sea clara, empática y efectiva. Incluir tablas explicativas de respuestas por nivel de gravedad puede ser útil aquí.

### Tablas Explicativas de Respuestas por Nivel de Gravedad

| Nivel de Gravedad (CV Analysis) | Respuesta Sugerida (Plantilla/Texto)                                  | Consideraciones                                                                 |
| :------------------------------ | :-------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| **No LPP Detectada**            | Mensaje informativo indicando que no se detectaron lesiones.           | Agradecer el envío, ofrecer ayuda adicional.                                    |
| **LPP Grado 1**                 | Mensaje indicando bajo riesgo, recomendaciones de cuidado preventivo. | Enfatizar la importancia de la prevención, sugerir monitoreo.                   |
| **LPP Grado 2**                 | Mensaje indicando riesgo moderado, sugerir consulta médica.           | Proporcionar información sobre síntomas, urgencia de consulta.                  |
| **LPP Grado 3/4 o Inclasificable** | Mensaje indicando alto riesgo, urgencia de atención médica inmediata. | Instrucciones claras sobre buscar ayuda profesional, no sustituye diagnóstico. |
| **Imagen No Clara/Inválida**    | Mensaje solicitando una imagen más clara o en formato correcto.       | Explicar por qué la imagen no pudo ser procesada, ofrecer reintentar.           |
