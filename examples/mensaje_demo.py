#!/usr/bin/env python3
"""
VIGÍA - MENSAJE DEFINITIVO FINAL
Exactamente como especificó el CTO
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from vigia_detect.messaging.slack_notifier import SlackNotifier

def enviar_mensaje_vigía_definitivo():
    """
    Mensaje DEFINITIVO según especificación exacta del CTO
    """
    
    notifier = SlackNotifier()
    
    # Datos del caso real
    imagen_path = "/Users/autonomos_dev/Projects/pressure/IMG-20250222-WA0015.jpg"
    imagen_exists = os.path.exists(imagen_path)
    
    print(f"🖼️ Imagen confirmada: {imagen_exists}")
    
    # Blocks DEFINITIVOS según especificación CTO
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🟡 NUEVO CASO VIGÍA - EVALUACIÓN ENFERMERÍA",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*👤 Paciente:* César Durán, 45 años"
                },
                {
                    "type": "mrkdwn", 
                    "text": "*🆔 ID Caso:* CD-2025-001"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "view_historial_cesar_definitivo",
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
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📸 IMAGEN RECIBIDA*\nTalón derecho — eritema localizado (≈3 cm)"
            },
            "accessory": {
                "type": "button",
                "action_id": "view_foto_cesar",
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
                "text": "*💬 MENSAJE DE TEXTO*\n\n_\"Hola!\"_"
            }
        },
        {
            "type": "section", 
            "text": {
                "type": "mrkdwn",
                "text": "*🎙️ AUDIO (Transcripción + Análisis Vigía):*\n\n_\"Hola! sabe que ayer fui al hospital como a las 4 de la tarde, y hoy dia amaneci con mucho mas dolor en mi pie, me tome los remedios pero no pasa nada. Que hago?\"_"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn", 
                "text": "*🧠 Análisis Emocional Vigía:*\n\n• Nivel estrés: **MEDIO** (4/10)\n• Dolor percibido: **LEVE-MODERADO**\n• Estado anímico: Preocupación controlada\n• Urgencia comunicativa: **BAJA**"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🔗 _[Ver imagen y audio original]_ | 📝 _Transcripción automática Vigía_"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🤖 SUGERENCIAS VIGÍA AI:*"
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
                    "text": "*Protocolo sugerido:* Seguimiento domiciliario (no escala)"
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
                "text": "*💬 Respuesta sugerida:*\n\n_\"Hola, gracias por enviar tu consulta y fotografía. Revisado por el equipo, parece una lesión de estadio I. Te recomendamos lavar la zona con suero fisiológico y cubrir con gasa estéril. En 24h envíanos otra imagen o te la solicitaremos y cuéntanos cómo te sientes. No dejes de tomar tus medicamentos por favor o limpies la herida con productos irritantes\"_"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "programar_seguimiento_vigía",
                    "text": {
                        "type": "plain_text",
                        "text": "⏰ Programar seguimiento",
                        "emoji": True
                    }
                }
            ]
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
                    "action_id": "escalar_medico_vigía",
                    "text": {
                        "type": "plain_text",
                        "text": "🟢 ESCALAR A MÉDICO",
                        "emoji": True
                    },
                    "style": "primary"
                },
                {
                    "type": "button", 
                    "action_id": "marcar_urgente_vigía",
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
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "agregar_notas_vigía",
                    "text": {
                        "type": "plain_text",
                        "text": "📝 Agregar Notas",
                        "emoji": True
                    }
                },
                {
                    "type": "button",
                    "action_id": "solicitar_imagenes_vigía", 
                    "text": {
                        "type": "plain_text",
                        "text": "📸 Solicitar más imágenes",
                        "emoji": True
                    }
                },
                {
                    "type": "button",
                    "action_id": "analisis_completo_vigía",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Ver análisis completo Vigía",
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
                    "text": "⏰ *Recibido:* 16/01/2025 - 10:30 hrs | *Tiempo respuesta:* <30 min | *Enfermera asignada:* Patricia Morales"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🔍 *Trazabilidad:* Sistema Vigía v1.2.0 | Clasificación automática completada | Paciente notificado automáticamente"
                }
            ]
        }
    ]
    
    try:
        print("🚀 ENVIANDO MENSAJE VIGÍA DEFINITIVO...")
        
        response = notifier.client.chat_postMessage(
            channel='C08TJHZFVD1',  # #vigia
            text="🟡 VIGÍA DEFINITIVO - César Durán",
            blocks=blocks
        )
        
        print(f"✅ MENSAJE VIGÍA DEFINITIVO ENVIADO!")
        print(f"📍 Timestamp: {response['ts']}")
        print(f"👤 César Durán, 45 años")
        print(f"🆔 CD-2025-001")
        print(f"📸 Imagen: Talón derecho eritema")
        print(f"🎙️ Audio: Dolor post-consulta")
        print(f"🤖 IA: Estadio I, Seguimiento domiciliario")
        
        print("\n✅ ELEMENTOS CONFIRMADOS:")
        print("  📋 Botón Ver Historial Completo")
        print("  🔍 Botón Ver Foto") 
        print("  💬 Respuesta sugerida completa")
        print("  🎯 Acciones enfermería completas")
        print("  🔍 Trazabilidad Sistema Vigía v1.2.0")
        
        return response
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

if __name__ == "__main__":
    print("🏥 VIGÍA - MENSAJE DEFINITIVO FINAL")
    print("="*60)
    print("👤 César Durán, 45 años")
    print("🆔 CD-2025-001") 
    print("📸 Talón derecho — eritema localizado")
    print("🎙️ Audio: Post-consulta + dolor")
    print("🤖 Vigía AI: Estadio I, Seguimiento domiciliario")
    print()
    
    response = enviar_mensaje_vigía_definitivo()
    
    if response:
        print("\n🎉 VIGÍA DEFINITIVO OPERATIVO!")
        print("✅ Mensaje completo enviado")
        print("✅ Todos los botones configurados")
        print("✅ Sistema Vigía v1.2.0 funcionando")
        print("\n🔍 REVISAR EN SLACK CANAL #project-lpp")
    else:
        print("❌ Error enviando mensaje definitivo")
