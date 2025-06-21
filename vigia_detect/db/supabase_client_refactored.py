"""
Cliente Supabase refactorizado usando BaseClient.
Elimina duplicación de código y mejora el manejo de errores.
"""
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from supabase import create_client, Client

# Importar la clase base
from ..core.base_client_v2 import BaseClientV2


class SupabaseClientRefactored(BaseClientV2):
    """
    Cliente mejorado para interactuar con Supabase.
    Extiende BaseClient para manejo consistente de configuración y logging.
    """
    
    def __init__(self):
        """Inicializa el cliente Supabase con configuración centralizada"""
        required_fields = [
            'supabase_url',
            'supabase_key'
        ]
        
        super().__init__(
            service_name="Supabase",
            required_fields=required_fields
        )
    
    def _initialize_client(self):
        """Inicializa el cliente Supabase específico"""
        try:
            self.client: Client = create_client(
                self.settings.supabase_url, 
                self.settings.supabase_key
            )
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    def validate_connection(self) -> bool:
        """Valida la conexión con Supabase"""
        try:
            # Intentar una operación simple para validar la conexión
            response = self.client.table('_realtime_schema').select('*').limit(1).execute()
            return True
        except Exception as e:
            self.logger.error(f"Supabase connection validation failed: {str(e)}")
            return False
            raise
    
    def health_check(self) -> bool:
        """Verifica que la conexión con Supabase esté funcionando"""
        try:
            # Usar Processing Database - tabla tokenized_patients
            result = self.client.table('tokenized_patients').select('token_id').limit(1).execute()
            self.log_info("Supabase health check passed")
            return True
        except Exception as e:
            self.log_error("Supabase health check failed", e)
            return False
    
    def get_or_create_patient(self, patient_code: str, **patient_data) -> Dict[str, Any]:
        """
        Obtiene un paciente existente o crea uno nuevo.
        
        Args:
            patient_code: Código único del paciente
            **patient_data: Datos adicionales del paciente (nombre, edad, etc.)
            
        Returns:
            Dict con los datos del paciente
        """
        try:
            # Buscar paciente existente
            result = self.client.table('patients')\
                .select('*')\
                .eq('patient_code', patient_code)\
                .execute()
            
            if result.data:
                self.log_info(f"Found existing patient: {patient_code}")
                return result.data[0]
            
            # Crear nuevo paciente
            new_patient = {
                'id': str(uuid.uuid4()),
                'patient_code': patient_code,
                'created_at': datetime.now().isoformat(),
                **patient_data
            }
            
            result = self.client.table('patients').insert(new_patient).execute()
            self.log_info(f"Created new patient: {patient_code}")
            
            return result.data[0] if result.data else new_patient
            
        except Exception as e:
            self.log_error(f"Error in get_or_create_patient for {patient_code}", e)
            raise
    
    def save_detection(self, 
                      patient_id: str,
                      detection_data: Dict[str, Any],
                      image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Guarda una detección en la base de datos.
        
        Args:
            patient_id: ID del paciente
            detection_data: Datos de la detección
            image_path: Ruta de la imagen (opcional)
            
        Returns:
            Dict con los datos de la detección guardada
        """
        try:
            # Preparar datos de detección
            detection = {
                'id': str(uuid.uuid4()),
                'patient_id': patient_id,
                'detected_at': datetime.now().isoformat(),
                'detection_data': json.dumps(detection_data),
                'severity': detection_data.get('max_severity', 0),
                'status': 'pending'
            }
            
            # Si hay imagen, crear registro de imagen primero
            if image_path:
                image_record = self._save_image_record(patient_id, image_path)
                detection['image_id'] = image_record['id']
            
            # Guardar detección
            result = self.client.table('detections').insert(detection).execute()
            self.log_info(f"Saved detection for patient {patient_id}")
            
            return result.data[0] if result.data else detection
            
        except Exception as e:
            self.log_error(f"Error saving detection for patient {patient_id}", e)
            raise
    
    def _save_image_record(self, patient_id: str, image_path: str) -> Dict[str, Any]:
        """Guarda registro de imagen en la base de datos"""
        try:
            image_record = {
                'id': str(uuid.uuid4()),
                'patient_id': patient_id,
                'file_path': image_path,
                'file_name': os.path.basename(image_path),
                'uploaded_at': datetime.now().isoformat()
            }
            
            # Calcular hash de la imagen si existe
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    image_record['file_hash'] = hashlib.sha256(f.read()).hexdigest()
            
            result = self.client.table('images').insert(image_record).execute()
            return result.data[0] if result.data else image_record
            
        except Exception as e:
            self.log_error(f"Error saving image record: {image_path}", e)
            raise
    
    def get_patient_detections(self, 
                              patient_code: str,
                              limit: int = 10,
                              status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene las detecciones de un paciente.
        
        Args:
            patient_code: Código del paciente
            limit: Número máximo de resultados
            status: Filtrar por estado (opcional)
            
        Returns:
            Lista de detecciones
        """
        try:
            # Primero obtener el paciente
            patient = self.get_or_create_patient(patient_code)
            
            # Construir query
            query = self.client.table('detections')\
                .select('*, images(*)')\
                .eq('patient_id', patient['id'])\
                .order('detected_at', desc=True)\
                .limit(limit)
            
            # Aplicar filtro de estado si se especifica
            if status:
                query = query.eq('status', status)
            
            result = query.execute()
            
            # Parsear detection_data de JSON
            detections = result.data if result.data else []
            for detection in detections:
                if isinstance(detection.get('detection_data'), str):
                    detection['detection_data'] = json.loads(detection['detection_data'])
            
            self.log_info(f"Retrieved {len(detections)} detections for patient {patient_code}")
            return detections
            
        except Exception as e:
            self.log_error(f"Error getting detections for patient {patient_code}", e)
            return []
    
    def update_detection_status(self, 
                               detection_id: str,
                               status: str,
                               notes: Optional[str] = None) -> bool:
        """
        Actualiza el estado de una detección.
        
        Args:
            detection_id: ID de la detección
            status: Nuevo estado
            notes: Notas adicionales (opcional)
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if notes:
                update_data['notes'] = notes
            
            result = self.client.table('detections')\
                .update(update_data)\
                .eq('id', detection_id)\
                .execute()
            
            self.log_info(f"Updated detection {detection_id} status to {status}")
            return bool(result.data)
            
        except Exception as e:
            self.log_error(f"Error updating detection {detection_id}", e)
            return False
    
    def get_statistics(self, 
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema.
        
        Args:
            start_date: Fecha inicial (opcional)
            end_date: Fecha final (opcional)
            
        Returns:
            Dict con estadísticas
        """
        try:
            # Query base para detecciones
            query = self.client.table('detections').select('severity, status, detected_at')
            
            # Aplicar filtros de fecha si se especifican
            if start_date:
                query = query.gte('detected_at', start_date.isoformat())
            if end_date:
                query = query.lte('detected_at', end_date.isoformat())
            
            result = query.execute()
            detections = result.data if result.data else []
            
            # Calcular estadísticas
            stats = {
                'total_detections': len(detections),
                'by_severity': {},
                'by_status': {},
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            }
            
            # Contar por severidad y estado
            for detection in detections:
                severity = detection.get('severity', 0)
                status = detection.get('status', 'unknown')
                
                stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            self.log_info(f"Generated statistics: {stats['total_detections']} total detections")
            return stats
            
        except Exception as e:
            self.log_error("Error generating statistics", e)
            return {
                'error': str(e),
                'total_detections': 0,
                'by_severity': {},
                'by_status': {}
            }

    # ===============================================
    # PROCESSING DATABASE METHODS (FASE 2)
    # ===============================================
    
    async def create_detection(self, detection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear detección LPP en Processing Database (solo datos tokenizados - NO PHI).
        
        Args:
            detection_data: Datos de detección con token_id, patient_alias, etc.
            
        Returns:
            Dict con la detección creada
        """
        try:
            # Preparar datos para lpp_detections table
            detection_record = {
                'detection_id': str(uuid.uuid4()),
                'token_id': detection_data['token_id'],
                'lpp_detected': detection_data['detected'],
                'lpp_grade': detection_data.get('lpp_grade'),
                'confidence_score': detection_data['confidence'],
                'anatomical_location': detection_data.get('anatomical_location', 'unknown'),
                'clinical_severity': detection_data.get('clinical_severity', 'unknown'),
                'urgency_level': detection_data.get('urgency_level', 'routine'),
                'treatment_protocol': json.dumps(detection_data.get('recommended_interventions', [])),
                'escalation_required': detection_data.get('escalation_required', False),
                'medical_review_required': detection_data.get('medical_review_required', False),
                'model_version': detection_data.get('processor_version', 'unknown'),
                'detection_algorithm': 'vigia_lpp_detector',
                'image_quality_score': detection_data.get('quality_metrics', {}).get('image_quality', 0),
                'analysis_completed_at': datetime.now().isoformat(),
                'total_processing_time_ms': int(detection_data.get('processing_time', 0) * 1000),
                'analyzed_by': 'clinical_processing_system'
            }
            
            # Insertar en lpp_detections
            result = self.client.table('lpp_detections').insert(detection_record).execute()
            
            self.log_info(f"Detection created for token {detection_data['token_id'][:8]}...")
            return result.data[0] if result.data else detection_record
            
        except Exception as e:
            self.log_error(f"Error creating detection for token {detection_data.get('token_id', 'unknown')}", e)
            raise

    async def create_clinical_note(self, notes_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear nota clínica en Processing Database (solo datos tokenizados - NO PHI).
        
        Args:
            notes_data: Datos de nota clínica con token_id, patient_alias, etc.
            
        Returns:
            Dict con la nota creada
        """
        try:
            # Para las notas clínicas, podemos usar una tabla personalizada o 
            # almacenar en medical_decisions como decisión de documentación
            note_record = {
                'decision_id': str(uuid.uuid4()),
                'token_id': notes_data['token_id'],
                'decision_type': 'clinical_documentation',
                'clinical_decision': notes_data['clinical_notes'],
                'guidelines_applied': json.dumps({'source': 'NPUAP_EPUAP_2019'}),
                'evidence_level': 'A',
                'confidence_level': 'high',
                'decision_algorithm': 'clinical_processing_system',
                'decision_version': '1.0.0',
                'decision_system': notes_data.get('created_by', 'vigia_system')
            }
            
            # Insertar en medical_decisions como documentación
            result = self.client.table('medical_decisions').insert(note_record).execute()
            
            self.log_info(f"Clinical note created for token {notes_data['token_id'][:8]}...")
            return result.data[0] if result.data else note_record
            
        except Exception as e:
            self.log_error(f"Error creating clinical note for token {notes_data.get('token_id', 'unknown')}", e)
            raise

    async def get_tokenized_patient(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener paciente tokenizado por token_id (NO PHI).
        
        Args:
            token_id: ID del token
            
        Returns:
            Dict con datos del paciente tokenizado o None
        """
        try:
            result = self.client.table('tokenized_patients')\
                .select('*')\
                .eq('token_id', token_id)\
                .eq('token_status', 'active')\
                .execute()
            
            if result.data:
                self.log_info(f"Found tokenized patient for token {token_id[:8]}...")
                return result.data[0]
            
            return None
            
        except Exception as e:
            self.log_error(f"Error retrieving tokenized patient for token {token_id}", e)
            return None

    async def get_patient_detections_by_token(self, token_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtener detecciones por token_id (NO PHI).
        
        Args:
            token_id: ID del token
            limit: Número máximo de resultados
            
        Returns:
            Lista de detecciones
        """
        try:
            result = self.client.table('lpp_detections')\
                .select('*')\
                .eq('token_id', token_id)\
                .order('analysis_completed_at', desc=True)\
                .limit(limit)\
                .execute()
            
            self.log_info(f"Retrieved {len(result.data)} detections for token {token_id[:8]}...")
            return result.data or []
            
        except Exception as e:
            self.log_error(f"Error retrieving detections for token {token_id}", e)
            return []

    async def create_processing_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear sesión de procesamiento (NO PHI).
        
        Args:
            session_data: Datos de la sesión
            
        Returns:
            Dict con la sesión creada
        """
        try:
            session_record = {
                'session_id': session_data['session_id'],
                'token_id': session_data.get('token_id'),
                'session_type': session_data.get('session_type', 'lpp_analysis'),
                'session_status': session_data.get('session_status', 'active'),
                'input_type': session_data.get('input_type', 'mixed'),
                'input_metadata': json.dumps(session_data.get('input_metadata', {})),
                'pipeline_stage': session_data.get('pipeline_stage', 'input_validation'),
                'session_expires_at': session_data.get('session_expires_at', 
                    (datetime.now() + timedelta(minutes=15)).isoformat()),
                'max_processing_time_minutes': session_data.get('max_processing_time_minutes', 30)
            }
            
            result = self.client.table('processing_sessions').insert(session_record).execute()
            
            self.log_info(f"Processing session created: {session_data['session_id']}")
            return result.data[0] if result.data else session_record
            
        except Exception as e:
            self.log_error(f"Error creating processing session {session_data.get('session_id', 'unknown')}", e)
            raise

    async def update_processing_session(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar sesión de procesamiento.
        
        Args:
            session_id: ID de la sesión
            updates: Campos a actualizar
            
        Returns:
            Dict con la sesión actualizada
        """
        try:
            # Preparar updates con timestamp
            update_data = {**updates}
            if 'session_status' in updates and updates['session_status'] == 'completed':
                update_data['session_completed_at'] = datetime.now().isoformat()
            
            result = self.client.table('processing_sessions')\
                .update(update_data)\
                .eq('session_id', session_id)\
                .execute()
            
            self.log_info(f"Processing session updated: {session_id}")
            return result.data[0] if result.data else {}
            
        except Exception as e:
            self.log_error(f"Error updating processing session {session_id}", e)
            raise

    async def create_external_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear notificación externa (NO PHI).
        
        Args:
            notification_data: Datos de la notificación
            
        Returns:
            Dict con la notificación creada
        """
        try:
            notification_record = {
                'notification_id': str(uuid.uuid4()),
                'token_id': notification_data.get('token_id'),
                'notification_type': notification_data['type'],
                'notification_status': 'pending',
                'recipient_type': ', '.join(notification_data.get('recipients', [])),
                'recipient_system': notification_data.get('recipient_system', 'slack'),
                'message_template': f"lpp_detection_{notification_data.get('priority', 'medium')}",
                'message_data': json.dumps({
                    'summary': notification_data.get('summary', ''),
                    'priority': notification_data.get('priority', 'medium'),
                    'phi_protected': True
                }),
                'urgency_level': notification_data.get('priority', 'medium'),
                'scheduled_at': datetime.now().isoformat(),
                'response_required': notification_data.get('response_required', False)
            }
            
            result = self.client.table('external_notifications').insert(notification_record).execute()
            
            self.log_info(f"External notification created: {notification_data['type']}")
            return result.data[0] if result.data else notification_record
            
        except Exception as e:
            self.log_error(f"Error creating external notification", e)
            raise

    async def log_system_audit(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registrar evento de auditoría del sistema (NO PHI).
        
        Args:
            audit_data: Datos del evento de auditoría
            
        Returns:
            Dict con el log de auditoría creado
        """
        try:
            audit_record = {
                'log_id': str(uuid.uuid4()),
                'session_id': audit_data.get('session_id'),
                'token_id': audit_data.get('token_id'),
                'event_type': audit_data['event_type'],
                'event_category': audit_data.get('event_category', 'system'),
                'event_description': audit_data.get('event_description', ''),
                'component': audit_data.get('component', 'unknown'),
                'service_version': audit_data.get('service_version', '1.0.0'),
                'processing_time_ms': audit_data.get('processing_time_ms'),
                'success': audit_data.get('success', True),
                'error_code': audit_data.get('error_code'),
                'error_message': audit_data.get('error_message'),
                'hipaa_compliant': audit_data.get('hipaa_compliant', True),
                'audit_required': audit_data.get('audit_required', True),
                'event_timestamp': audit_data.get('event_timestamp', datetime.now().isoformat())
            }
            
            result = self.client.table('system_audit_logs').insert(audit_record).execute()
            
            return result.data[0] if result.data else audit_record
            
        except Exception as e:
            self.log_error(f"Error creating system audit log", e)
            # No re-raise para auditoría - log local y continuar
            return {}


# Función de migración para facilitar la transición
def migrate_to_refactored_client():
    """
    Ejemplo de cómo migrar del cliente antiguo al refactorizado.
    """
    # Antiguo
    # from vigia_detect.db.supabase_client import SupabaseClient
    # client = SupabaseClient()
    
    # Nuevo
    from vigia_detect.db.supabase_client_refactored import SupabaseClientRefactored
    client = SupabaseClientRefactored()
    
    # La API es la misma, pero ahora con mejor manejo de errores y logging
    return client


if __name__ == "__main__":
    # Ejemplo de uso
    try:
        client = SupabaseClientRefactored()
        
        # Health check
        if client.health_check():
            print("✅ Conexión con Supabase establecida")
            
            # Ejemplo: obtener estadísticas
            stats = client.get_statistics()
            print(f"📊 Total detecciones: {stats['total_detections']}")
            print(f"📈 Por severidad: {stats['by_severity']}")
            print(f"📋 Por estado: {stats['by_status']}")
            
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("Por favor, configura SUPABASE_URL y SUPABASE_KEY en tu archivo .env")

# Alias for backward compatibility
SupabaseClient = SupabaseClientRefactored