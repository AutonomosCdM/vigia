"""
Cliente Supabase refactorizado usando BaseClient.
Elimina duplicación de código y mejora el manejo de errores.
"""
import uuid
import json
from datetime import datetime
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
            # Intentar una consulta simple
            result = self.client.table('patients').select('id').limit(1).execute()
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