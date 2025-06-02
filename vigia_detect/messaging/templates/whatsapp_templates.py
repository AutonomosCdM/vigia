"""
Plantillas de mensajes para WhatsApp.

Este módulo proporciona plantillas predefinidas para enviar
mensajes estructurados a través de WhatsApp.
"""

from typing import Dict, Any, List, Optional

# Plantillas para análisis LPP
def welcome_template() -> str:
    """Plantilla de bienvenida para nuevos usuarios"""
    return """
¡Bienvenido a LPP-Detect! 🏥

Este sistema le permite:
• Enviar imágenes de lesiones por presión para análisis
• Recibir evaluaciones preliminares
• Seguir recomendaciones de profesionales

*Envíe una imagen clara de la lesión para comenzar.*
Para obtener ayuda, escriba 'ayuda'.
    """.strip()

def help_template() -> str:
    """Plantilla de ayuda con comandos disponibles"""
    return """
*Comandos disponibles:*

• Envíe una imagen para análisis
• 'ayuda' - Muestra este mensaje
• 'info' - Información sobre LPP-Detect
• 'registro' - Información sobre registro

*Nota:* Para mejores resultados, envíe imágenes con buena iluminación y enfoque.
    """.strip()

def results_template(detections: List[Dict[str, Any]], image_url: Optional[str] = None) -> str:
    """
    Genera plantilla para resultados de detección
    
    Args:
        detections: Lista de detecciones con datos de stage y confidence
        image_url: URL opcional de la imagen de resultado
        
    Returns:
        str: Mensaje formateado para WhatsApp
    """
    if not detections:
        return """
🔍 *ANÁLISIS PRELIMINAR*

No se detectaron lesiones por presión en la imagen.

_Nota: Si sospecha de una lesión, considere tomar otra foto con mejor iluminación o consulte a su profesional de salud._
        """.strip()
    
    # Textos descriptivos por etapa
    stage_descriptions = {
        0: "Categoría 1 (Eritema no blanqueable): Piel intacta con enrojecimiento no blanqueable.",
        1: "Categoría 2 (Úlcera de espesor parcial): Pérdida parcial del espesor de la piel.",
        2: "Categoría 3 (Pérdida total del espesor de la piel): Tejido subcutáneo visible.",
        3: "Categoría 4 (Pérdida total del espesor de los tejidos): Exposición de músculo/hueso.",
    }
    
    # Recomendaciones por etapa
    stage_recommendations = {
        0: "• Aliviar presión en zona afectada\n• Mantener piel limpia y seca\n• Aplicar crema hidratante",
        1: "• Aliviar presión en zona afectada\n• Limpieza con solución salina\n• Aplicar apósito hidrocoloide\n• Consultar profesional de salud",
        2: "• CONSULTAR PROFESIONAL DE SALUD URGENTE\n• No aplicar presión en zona\n• Mantener herida limpia",
        3: "• REQUIERE ATENCIÓN MÉDICA INMEDIATA\n• No aplicar presión en zona\n• No limpiar por su cuenta",
    }
    
    # Construir mensaje
    message = "🔍 *ANÁLISIS PRELIMINAR:*\n\n"
    
    # Reportar cada detección
    for i, detection in enumerate(detections):
        stage = detection["stage"]
        confidence = detection["confidence"] * 100
        
        message += f"*Lesión {i+1}:*\n"
        message += f"• Clasificación: {stage_descriptions.get(stage, f'Categoría {stage+1}')}\n"
        message += f"• Confianza: {confidence:.1f}%\n\n"
        message += f"*Recomendaciones:*\n{stage_recommendations.get(stage, 'Consultar profesional de salud')}\n\n"
    
    # Agregar disclaimer
    message += "_ATENCIÓN: Este es un análisis preliminar automatizado. " \
              "La evaluación final siempre debe ser realizada por profesionales médicos._"
    
    return message

def error_template(error_message: str = "") -> str:
    """Plantilla para mensajes de error"""
    message = """
⚠️ *ERROR EN PROCESAMIENTO*

No fue posible procesar su imagen.
    """.strip()
    
    if error_message:
        message += f"\n\nDetalle: {error_message}"
    
    message += "\n\nIntente nuevamente con una imagen más clara o contacte a soporte."
    
    return message

def processing_template() -> str:
    """Plantilla para notificar que se está procesando la imagen"""
    return """
🔄 *PROCESANDO IMAGEN*

Estamos analizando su imagen...
Recibirá los resultados en breve.

Gracias por su paciencia.
    """.strip()

def info_template() -> str:
    """Plantilla con información sobre el sistema"""
    return """
*Sobre LPP-Detect*

LPP-Detect es un sistema para detección temprana de lesiones por presión (LPP) desarrollado por especialistas en salud.

*¿Qué son las LPP?*
Las lesiones por presión (úlceras por presión) son daños en la piel y tejidos subyacentes causados por presión prolongada.

*¿Cómo funciona?*
1. Envíe foto de la zona afectada
2. Nuestro sistema analiza la imagen
3. Reciba evaluación preliminar y recomendaciones

*Limitaciones*
Este sistema no reemplaza la evaluación profesional médica. Siempre consulte con su equipo de salud.

*Privacidad*
Sus imágenes se procesan de forma segura y confidencial cumpliendo con normativas de protección de datos.
    """.strip()
