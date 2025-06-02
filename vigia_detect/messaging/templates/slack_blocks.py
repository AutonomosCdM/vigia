"""
Templates reutilizables para bloques de Slack
"""
from typing import List, Dict, Optional, Any
from datetime import datetime


class SlackBlockBuilder:
    """Constructor de bloques de Slack reutilizables"""
    
    @staticmethod
    def header(text: str, emoji: str = "") -> Dict[str, Any]:
        """Crear un bloque de header"""
        header_text = f"{emoji} {text}" if emoji else text
        return {
            "type": "header",
            "text": {"type": "plain_text", "text": header_text}
        }
    
    @staticmethod
    def divider() -> Dict[str, str]:
        """Crear un divisor"""
        return {"type": "divider"}
    
    @staticmethod
    def section_with_fields(fields: List[Dict[str, str]]) -> Dict[str, Any]:
        """Crear sección con campos"""
        return {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": field} for field in fields
            ]
        }
    
    @staticmethod
    def section_with_text(text: str) -> Dict[str, Any]:
        """Crear sección con texto"""
        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text}
        }
    
    @staticmethod
    def section_with_image(text: str, image_url: str, alt_text: str) -> Dict[str, Any]:
        """Crear sección con imagen"""
        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
            "accessory": {
                "type": "image",
                "image_url": image_url,
                "alt_text": alt_text
            }
        }
    
    @staticmethod
    def actions(buttons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crear bloque de acciones con botones"""
        return {
            "type": "actions",
            "elements": buttons
        }
    
    @staticmethod
    def button(text: str, action_id: str, style: Optional[str] = None, 
               value: Optional[str] = None) -> Dict[str, Any]:
        """Crear un botón"""
        button = {
            "type": "button",
            "text": {"type": "plain_text", "text": text},
            "action_id": action_id
        }
        if style:
            button["style"] = style
        if value:
            button["value"] = value
        return button
    
    @staticmethod
    def context(elements: List[str]) -> Dict[str, Any]:
        """Crear bloque de contexto"""
        return {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": element} for element in elements
            ]
        }


class VigiaMessageTemplates:
    """Templates específicos para mensajes de Vigía"""
    
    @staticmethod
    def caso_header(paciente: str, id_caso: str, servicio: str, 
                   cama: str, fecha: Optional[str] = None) -> List[Dict[str, Any]]:
        """Header estándar para casos de Vigía"""
        if not fecha:
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        return [
            SlackBlockBuilder.header(f"Nueva Detección - Caso #{id_caso}", "🚨"),
            SlackBlockBuilder.section_with_fields([
                f"*Paciente:*\n{paciente}",
                f"*ID Caso:*\n{id_caso}",
                f"*Servicio:*\n{servicio}",
                f"*Cama:*\n{cama}",
                f"*Fecha/Hora:*\n{fecha}",
                f"*Estado:*\n🔴 Pendiente"
            ])
        ]
    
    @staticmethod
    def deteccion_info(grado: int, ubicacion: str, confianza: float,
                      descripcion: str) -> List[Dict[str, Any]]:
        """Información de detección de LPP"""
        severidad_emoji = {
            0: "⚪",  # Sin lesión (eritema)
            1: "🟡",  # Grado 1
            2: "🟠",  # Grado 2
            3: "🔴",  # Grado 3
            4: "⚫"   # Grado 4
        }
        
        emoji = severidad_emoji.get(grado, "❓")
        
        return [
            SlackBlockBuilder.divider(),
            SlackBlockBuilder.section_with_text(
                f"*🔍 Detección de Lesión por Presión*\n\n" +
                f"• *Grado:* {emoji} Grado {grado}\n" +
                f"• *Ubicación anatómica:* {ubicacion}\n" +
                f"• *Confianza del modelo:* {confianza:.1%}\n" +
                f"• *Descripción:* {descripcion}"
            )
        ]
    
    @staticmethod
    def analisis_emocional(sentimiento: str, preocupaciones: List[str],
                          estado_animo: str) -> List[Dict[str, Any]]:
        """Análisis emocional del paciente"""
        preocu_text = "\n".join([f"  - {p}" for p in preocupaciones])
        
        return [
            SlackBlockBuilder.divider(),
            SlackBlockBuilder.section_with_text(
                f"*💭 Análisis Emocional del Paciente*\n\n" +
                f"• *Sentimiento detectado:* {sentimiento}\n" +
                f"• *Estado de ánimo:* {estado_animo}\n" +
                f"• *Preocupaciones expresadas:*\n{preocu_text}"
            )
        ]
    
    @staticmethod
    def acciones_enfermeria() -> Dict[str, Any]:
        """Botones de acción estándar para enfermería"""
        return SlackBlockBuilder.actions([
            SlackBlockBuilder.button(
                "📋 Ver Historial Médico",
                "ver_historial_medico",
                style="primary"
            ),
            SlackBlockBuilder.button(
                "🏥 Solicitar Evaluación Médica",
                "solicitar_evaluacion_medica",
                style="danger"
            ),
            SlackBlockBuilder.button(
                "✅ Marcar como Resuelto",
                "marcar_resuelto"
            )
        ])
    
    @staticmethod
    def mensaje_completo_lpp(
        paciente: str,
        id_caso: str,
        servicio: str,
        cama: str,
        grado: int,
        ubicacion: str,
        confianza: float,
        descripcion: str,
        imagen_url: Optional[str] = None,
        analisis_emocional: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Construir mensaje completo de detección de LPP"""
        
        # Header
        blocks = VigiaMessageTemplates.caso_header(
            paciente, id_caso, servicio, cama
        )
        
        # Info de detección
        blocks.extend(VigiaMessageTemplates.deteccion_info(
            grado, ubicacion, confianza, descripcion
        ))
        
        # Imagen si está disponible
        if imagen_url:
            blocks.append(
                SlackBlockBuilder.section_with_image(
                    "*📸 Imagen de la lesión:*",
                    imagen_url,
                    "Imagen de lesión detectada"
                )
            )
        
        # Análisis emocional si está disponible
        if analisis_emocional:
            blocks.extend(VigiaMessageTemplates.analisis_emocional(
                analisis_emocional.get("sentimiento", "No detectado"),
                analisis_emocional.get("preocupaciones", []),
                analisis_emocional.get("estado_animo", "No evaluado")
            ))
        
        # Acciones
        blocks.append(VigiaMessageTemplates.acciones_enfermeria())
        
        # Contexto
        blocks.append(
            SlackBlockBuilder.context([
                "Sistema Vigía v1.0 | Detección automática con IA"
            ])
        )
        
        return blocks
    
    @staticmethod
    def notificacion_evaluacion_medica(
        solicitante: str,
        paciente: str,
        id_paciente: str,
        ubicacion: str,
        prioridad: str = "ALTA"
    ) -> List[Dict[str, Any]]:
        """Notificación de solicitud de evaluación médica"""
        return [
            SlackBlockBuilder.header("Evaluación Médica Solicitada", "🚨"),
            SlackBlockBuilder.section_with_text(
                f"*Solicitado por:* <@{solicitante}>\n" +
                f"*Paciente:* {paciente}\n" +
                f"*ID:* {id_paciente}\n" +
                f"*Ubicación:* {ubicacion}\n" +
                f"*Prioridad:* *{prioridad}*"
            ),
            SlackBlockBuilder.actions([
                SlackBlockBuilder.button(
                    "Aceptar Evaluación",
                    "aceptar_evaluacion",
                    style="primary"
                ),
                SlackBlockBuilder.button(
                    "Ver Detalles",
                    "ver_detalles_evaluacion"
                )
            ])
        ]
    
    @staticmethod
    def caso_resuelto(
        resuelto_por: str,
        paciente: str,
        id_paciente: str,
        resolucion: str,
        tiempo_resolucion: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Mensaje de caso resuelto"""
        blocks = [
            SlackBlockBuilder.header("Caso Resuelto", "✅"),
            SlackBlockBuilder.section_with_fields([
                f"*Resuelto por:* <@{resuelto_por}>",
                f"*Paciente:* {paciente}",
                f"*ID:* {id_paciente}",
                f"*Tiempo de resolución:* {tiempo_resolucion or 'N/A'}"
            ]),
            SlackBlockBuilder.divider(),
            SlackBlockBuilder.section_with_text(
                f"*Resolución:*\n{resolucion}"
            )
        ]
        
        return blocks