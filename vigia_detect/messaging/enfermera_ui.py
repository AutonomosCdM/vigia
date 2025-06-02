"""
Pantalla Enfermera - Layout específico según mockup
Implementa exactamente el layout requerido por CTO
"""

def crear_pantalla_enfermera_final():
    """
    Pantalla enfermera final según especificaciones exactas
    Layout: Sugerencias AI arriba → Imagen/Audio → Botones acción
    """
    
    # Datos del caso real
    imagen_path = "/Users/autonomos_dev/Projects/pressure/IMG-20250222-WA0015.jpg"
    imagen_size = "58,468 bytes"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🟡 NUEVO CASO LPP - EVALUACIÓN ENFERMERÍA",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*👤 Paciente:*\nCésar Durán, 45 años"
                },
                {
                    "type": "mrkdwn", 
                    "text": "*🆔 ID Caso:*\nCD-2025-001"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "view_full_history_real",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 Ver Historial Completo",
                        "emoji": True
                    },
                    "style": "primary"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_(al apretar debe salir lo que te muestro abajo)_"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📸 IMAGEN ENVIADA*\nTalón derecho — eritema localizado (≈3 cm)"
            },
            "accessory": {
                "type": "button",
                "action_id": "view_real_photo",
                "text": {
                    "type": "plain_text",
                    "text": "🔍 Ver Foto",
                    "emoji": True
                },
                "style": "primary"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*💬 MENSAJE DE TEXTO*\n_\"Mi herida parece que está más roja y me está comenzando a doler...\"_"
            }
        },
        {
            "type": "section", 
            "text": {
                "type": "mrkdwn",
                "text": "*🎙️ AUDIO (Transcripción + Análisis ADK):*\n_\"No es mucho el dolor, pero desde ayer la noto más roja\"_"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn", 
                "text": "*🧠 Análisis Emocional ADK:*\n• Nivel estrés: **MEDIO** (4/10)\n• Dolor percibido: **LEVE-MODERADO**\n• Estado anímico: Preocupación controlada\n• Urgencia comunicativa: **BAJA**"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🔗 _[Ver imagen y audio original]_ | 📝 _Transcripción automática ADK_"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🤖 SUGERENCIAS PRESSURE AI:*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Estadio:* I (eritema no blanqueable)"
                },
                {
                    "type": "mrkdwn", 
                    "text": "*Riesgo:* Bajo (2/10)"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Protocolo sugerido:* Manejo por enfermería"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Confianza IA:* 87.3%"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*💬 Respuesta sugerida:*\n_\"Hola César, gracias por enviar la foto. Parece una lesión de estadio I. Te recomendamos lavar la zona con suero fisiológico y cubrir con gasa estéril. En 24h envíanos otra imagen y cuéntanos cómo te sientes.\"_"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "schedule_followup_24h",
                    "text": {
                        "type": "plain_text",
                        "text": "⏰ Programar seguimiento",
                        "emoji": True
                    }
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "va a pedir la foto en 24 horas."
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🎯 ACCIONES ENFERMERÍA*"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "escalate_to_doctor_real",
                    "text": {
                        "type": "plain_text",
                        "text": "🟢 ESCALAR A MÉDICO",
                        "emoji": True
                    },
                    "style": "primary"
                },
                {
                    "type": "button", 
                    "action_id": "mark_as_urgent_real",
                    "text": {
                        "type": "plain_text",
                        "text": "🔴 MARCAR COMO URGENTE",
                        "emoji": True
                    },
                    "style": "danger"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "al escalar a medico, sale la lista de los docs disponibles"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "add_notes_real",
                    "text": {
                        "type": "plain_text",
                        "text": "📝 Agregar Notas",
                        "emoji": True
                    }
                },
                {
                    "type": "button",
                    "action_id": "request_more_images_real", 
                    "text": {
                        "type": "plain_text",
                        "text": "📸 Solicitar más imágenes",
                        "emoji": True
                    }
                },
                {
                    "type": "button",
                    "action_id": "view_complete_adk_analysis",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Ver análisis completo ADK",
                        "emoji": True
                    }
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"⏰ *Recibido:* 16/01/2025 - 10:30 hrs | *Tiempo respuesta:* <30 min | *Enfermera asignada:* Patricia Morales"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🔍 *Trazabilidad:* Sistema ADK v1.2.0 | Clasificación automática completada | Paciente notificado automáticamente"
                }
            ]
        }
    ]
    
    return blocks

def crear_historial_completo_paciente():
    """
    Modal o vista cuando se presiona "Ver Historial Completo"
    """
    return {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "📋 Historial Completo - César Durán"
        },
        "blocks": [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*👤 Paciente:*\nCésar Durán, 45 años"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*🆔 ID Caso:*\nCD-2025-001"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*🏥 Servicio:*\nTraumatología - Cama 302-A"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*📅 Ingreso:*\n15/01/2025"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*💊 Medicamentos actuales:*\n• Metformina 850mg (2 veces/día)\n• Losartán 50mg (1 vez/día)"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*⚠️ Alergias:*\nNinguna conocida"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*🩺 Antecedentes:*\nDM2, HTA\nRiesgo Braden: 14/23"
                    },
                    {
                        "type": "mrkdwn", 
                        "text": "*📊 Signos vitales:*\nPA: 145/90 mmHg\nFC: 78 bpm\nTemp: 36.8°C"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 HISTORIAL DEL CASO*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*12/01:* Consulta preventiva inicial"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*14/01:* Control sin lesión"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*16/01:* **ESTE CASO** - Eritema emergente"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Evolución:* Progresión 48h"
                    }
                ]
            }
        ]
    }

def crear_lista_medicos_disponibles():
    """
    Lista de médicos cuando se presiona "ESCALAR A MÉDICO"
    """
    return {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "👨‍⚕️ Asignar Médico para Evaluación"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🏥 Médicos disponibles para evaluar caso César Durán:*"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Dr. Andrés Silva - Disponible* ✅"
                },
                "accessory": {
                    "type": "button",
                    "action_id": "assign_dr_silva",
                    "text": {
                        "type": "plain_text",
                        "text": "Asignar",
                        "emoji": True
                    },
                    "style": "primary"
                }
            },
            {
                "type": "section", 
                "text": {
                    "type": "mrkdwn",
                    "text": "*Dr. Carlos Mendoza - Disponible* ✅"
                },
                "accessory": {
                    "type": "button",
                    "action_id": "assign_dr_mendoza",
                    "text": {
                        "type": "plain_text",
                        "text": "Asignar",
                        "emoji": True
                    },
                    "style": "primary"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Dr. María Rodríguez - En consulta* 🟡"
                },
                "accessory": {
                    "type": "button",
                    "action_id": "assign_dr_rodriguez",
                    "text": {
                        "type": "plain_text",
                        "text": "Asignar",
                        "emoji": True
                    }
                }
            }
        ]
    }

# Configuración para mostrar imagen real
def obtener_url_imagen_real():
    """
    Retorna la URL o path de la imagen real para mostrar en Slack
    """
    imagen_path = "/Users/autonomos_dev/Projects/pressure/IMG-20250222-WA0015.jpg"
    imagen_info = {
        "path": imagen_path,
        "size": "58,468 bytes", 
        "timestamp": "22/02/2025 - WA0015",
        "description": "Talón derecho - eritema localizado ≈3 cm"
    }
    return imagen_info
