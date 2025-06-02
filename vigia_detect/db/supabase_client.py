"""
Cliente para interactuar con la base de datos Supabase.

Este módulo proporciona una interfaz para guardar y recuperar datos 
relacionados con las detecciones del sistema Vigía en la base de datos Supabase.
"""

import os
import logging
import uuid
import json
from pathlib import Path
from datetime import datetime
import hashlib
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logger = logging.getLogger('vigia-detect.supabase')

class SupabaseClient:
    """
    Cliente para interactuar con la base de datos Supabase.
    
    Proporciona métodos para guardar y recuperar información relacionada con
    detecciones de Vigía, pacientes, imágenes y otros datos clínicos.
    """
    
    def __init__(self):
        """Inicializa el cliente Supabase usando credenciales del entorno."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Faltan variables de entorno SUPABASE_URL y/o SUPABASE_KEY. " +
                "Asegúrate de crear un archivo .env basado en .env.example."
            )
        
        # Inicializar cliente
        self.client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Cliente Supabase inicializado correctamente")
    
    def _get_or_create_patient(self, patient_code):
        """
        Obtiene un paciente existente o crea uno nuevo si no existe.
        
        Args:
            patient_code: Código único del paciente
            
        Returns:
            str: ID del paciente (UUID)
        """
        if not patient_code:
            # Generar código aleatorio si no se proporciona
            patient_code = f"TEMP-{uuid.uuid4().hex[:8].upper()}"
            logger.info(f"Código de paciente generado: {patient_code}")
        
        # Buscar paciente existente
        result = self.client.table("clinical_data.patients").select("id").eq("patient_code", patient_code).execute()
        
        # Si existe, retornar su ID
        if result.data and len(result.data) > 0:
            patient_id = result.data[0]["id"]
            logger.info(f"Paciente existente encontrado: {patient_id}")
            return patient_id
        
        # Si no existe, crear nuevo
        logger.info(f"Creando nuevo paciente con código: {patient_code}")
        new_patient = {
            "patient_code": patient_code,
            "age_range": "61-80",  # Valor por defecto, actualizar en producción
            "gender": "other",     # Valor por defecto, actualizar en producción
            "risk_factors": json.dumps({"known": False}),
            "mobility_status": "unknown"
        }
        
        result = self.client.table("clinical_data.patients").insert(new_patient).execute()
        
        if result.data and len(result.data) > 0:
            patient_id = result.data[0]["id"]
            logger.info(f"Nuevo paciente creado: {patient_id}")
            return patient_id
        else:
            raise Exception("Error al crear nuevo paciente")
    
    def _get_or_create_model(self, model_name, model_version):
        """
        Obtiene un modelo existente o crea uno nuevo si no existe.
        
        Args:
            model_name: Nombre del modelo (ej. 'yolov5s')
            model_version: Versión del modelo
            
        Returns:
            str: ID del modelo (UUID)
        """
        # Buscar modelo existente
        result = self.client.table("ml_operations.models").select("id").eq("model_name", model_name).eq("model_version", model_version).execute()
        
        # Si existe, retornar su ID
        if result.data and len(result.data) > 0:
            model_id = result.data[0]["id"]
            logger.info(f"Modelo existente encontrado: {model_id}")
            return model_id
        
        # Si no existe, crear nuevo
        logger.info(f"Registrando nuevo modelo: {model_name} v{model_version}")
        new_model = {
            "model_name": model_name,
            "model_version": model_version,
            "model_type": "detection",
            "model_path": "yolov5-wound",  # Ruta de referencia
            "active": True,
            "parameters": json.dumps({"source": "calisma/pressure-ulcer"})
        }
        
        result = self.client.table("ml_operations.models").insert(new_model).execute()
        
        if result.data and len(result.data) > 0:
            model_id = result.data[0]["id"]
            logger.info(f"Nuevo modelo registrado: {model_id}")
            return model_id
        else:
            raise Exception("Error al registrar nuevo modelo")
    
    def _save_image(self, image_path, patient_id, file_hash=None, body_location=None):
        """
        Guarda información de una imagen en la base de datos.
        
        Args:
            image_path: Ruta a la imagen
            patient_id: ID del paciente
            file_hash: Hash SHA-256 de la imagen (opcional)
            body_location: Ubicación en el cuerpo (opcional)
            
        Returns:
            str: ID de la imagen (UUID)
        """
        # Calcular hash si no se proporciona
        if not file_hash:
            with open(image_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Preparar datos
        image_data = {
            "patient_id": patient_id,
            "file_path": str(image_path),
            "file_hash": file_hash,
            "image_type": "original",
            "body_location": body_location or "unknown",
            "metadata": json.dumps({"source": "cli_upload"})
        }
        
        # Guardar en BD
        result = self.client.table("ml_operations.lpp_images").insert(image_data).execute()
        
        if result.data and len(result.data) > 0:
            image_id = result.data[0]["id"]
            logger.info(f"Imagen guardada en BD: {image_id}")
            return image_id
        else:
            raise Exception("Error al guardar imagen en BD")
    
    def save_detection(self, image_path, detection_results, patient_code=None, output_path=None):
        """
        Guarda los resultados de una detección de LPP en la base de datos.
        
        Args:
            image_path: Ruta a la imagen original
            detection_results: Resultados de la detección
            patient_code: Código único del paciente (opcional)
            output_path: Ruta a la imagen con anotaciones (opcional)
            
        Returns:
            dict: Información sobre los datos guardados
        """
        try:
            # Obtener/crear paciente
            patient_id = self._get_or_create_patient(patient_code)
            
            # Guardar imagen original
            image_id = self._save_image(image_path, patient_id)
            
            # Obtener/crear referencia al modelo
            model_id = self._get_or_create_model("yolov5s", "1.0.0")  # Valores por defecto
            
            # Preparar datos de detección
            for detection in detection_results["detections"]:
                detection_data = {
                    "image_id": image_id,
                    "model_id": model_id,
                    "detection_results": json.dumps(detection),
                    "lpp_stage": detection.get("stage", 0),
                    "confidence_score": detection.get("confidence", 0.0),
                    "processing_time_ms": detection_results.get("processing_time_ms", 0)
                }
                
                # Guardar detección
                result = self.client.table("ml_operations.lpp_detections").insert(detection_data).execute()
                
                if not (result.data and len(result.data) > 0):
                    logger.warning("Error al guardar detección en BD")
            
            # Crear entrada de log
            log_data = {
                "event_type": "detection",
                "entity_type": "image",
                "entity_id": image_id,
                "ip_address": "127.0.0.1",  # Local para CLI
                "details": json.dumps({
                    "detections_count": len(detection_results["detections"]),
                    "source": "cli_upload"
                })
            }
            
            self.client.table("audit_logs.system_logs").insert(log_data).execute()
            
            return {
                "success": True,
                "patient_id": patient_id,
                "image_id": image_id,
                "detections_saved": len(detection_results["detections"])
            }
            
        except Exception as e:
            logger.error(f"Error guardando detección en Supabase: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_patient_detections(self, patient_code):
        """
        Obtiene todas las detecciones de LPP para un paciente.
        
        Args:
            patient_code: Código único del paciente
            
        Returns:
            list: Lista de detecciones con sus metadatos
        """
        try:
            # Consulta con joins para obtener toda la información relevante
            query = """
            SELECT 
                p.patient_code,
                i.file_path,
                i.body_location,
                d.detection_results,
                d.lpp_stage,
                d.confidence_score,
                d.created_at,
                m.model_name
            FROM 
                ml_operations.lpp_detections d
                JOIN ml_operations.lpp_images i ON d.image_id = i.id
                JOIN clinical_data.patients p ON i.patient_id = p.id
                JOIN ml_operations.models m ON d.model_id = m.id
            WHERE 
                p.patient_code = ?
            ORDER BY
                d.created_at DESC
            """
            
            # Ejecutar consulta
            result = self.client.table("ml_operations.lpp_detections").select(query, patient_code).execute()
            
            if result.data:
                return result.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo detecciones: {str(e)}")
            return []
