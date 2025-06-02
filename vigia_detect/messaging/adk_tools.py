"""
ADK Tool integration for Slack notifications in LPP-Detect system.
This module provides Google ADK compatible tools for medical alert notifications.
"""

from typing import Dict
# from google.adk.tools import BaseTool  # Not needed for standalone functions
from .slack_notifier import SlackNotifier

# ADK Tool class implementation would go here if using BaseTool
# For now, using standalone functions for simplicity


# Standalone functions for direct ADK integration
def enviar_alerta_lpp(canal: str, severidad: int, paciente_id: str, 
                     detalles: Dict) -> Dict:
    """
    Función standalone para notificaciones LPP desde ADK.
    Puede ser registrada directamente como FunctionTool en agentes ADK.
    
    Args:
        canal (str): Canal Slack destino
        severidad (int): Severidad LPP (0-4)
        paciente_id (str): ID paciente anonimizado
        detalles (dict): Detalles detección
    
    Returns:
        dict: Resultado operación para procesamiento ADK
    """
    notifier = SlackNotifier()
    return notifier.notificar_deteccion_lpp(canal, severidad, paciente_id, detalles)


def test_slack_desde_adk(canal: str = "#general") -> Dict:
    """
    Test de conectividad Slack para debugging ADK.
    
    Args:
        canal (str): Canal para test
        
    Returns:
        dict: Resultado test
    """
    notifier = SlackNotifier()
    return notifier.enviar_mensaje_test(canal)
