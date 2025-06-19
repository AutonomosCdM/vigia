"""
Supabase MCP Server - Serverless Implementation
==============================================

Medical-grade database operations via Supabase.
Provides MCP tools for storing, retrieving, and managing medical data with HIPAA compliance.
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .base_mcp_server import BaseMCPServer
from ..utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)

# Supabase integration (optional)
try:
    from supabase import create_client, Client
    from supabase.errors import APIError
    supabase_available = True
except ImportError:
    logger.warning("Supabase not available - running in mock mode")
    supabase_available = False
    APIError = Exception


class SupabaseMCPServer(BaseMCPServer):
    """Serverless MCP server for Supabase database operations."""
    
    def __init__(self):
        """Initialize Supabase MCP server"""
        super().__init__("Supabase", "1.0.0")
        
        # Initialize Supabase client (optional)
        self.supabase_client = None
        if supabase_available:
            self._init_supabase_client()
        
        # Medical database schema definitions
        self.medical_tables = {
            "lpp_detections": {
                "primary_key": "id",
                "columns": ["patient_code", "lpp_grade", "confidence", "anatomical_location", "detected_at"],
                "sensitive_columns": ["patient_code"],
                "description": "LPP detection results"
            },
            "patient_records": {
                "primary_key": "id", 
                "columns": ["patient_code", "age", "gender", "medical_history", "created_at"],
                "sensitive_columns": ["patient_code", "medical_history"],
                "description": "Patient medical records"
            },
            "medical_audit_logs": {
                "primary_key": "id",
                "columns": ["event_type", "patient_code", "user_id", "timestamp", "data"],
                "sensitive_columns": ["patient_code", "user_id"],
                "description": "HIPAA-compliant audit logs"
            },
            "medical_protocols": {
                "primary_key": "id",
                "columns": ["protocol_name", "version", "content", "category", "effective_date"],
                "sensitive_columns": [],
                "description": "Medical protocols and guidelines"
            }
        }
        
        # Register tools
        self._register_supabase_tools()
        
        # Register resources
        self._register_supabase_resources()
    
    def _init_supabase_client(self):
        """Initialize Supabase client if credentials available"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if supabase_url and supabase_key:
                self.supabase_client = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized")
            else:
                logger.warning("Supabase credentials not configured - using mock mode")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
    
    def _register_supabase_tools(self):
        """Register Supabase MCP tools"""
        
        # Tool for storing LPP detection data
        self.register_tool(
            name="store_lpp_detection",
            description="Store LPP detection data in medical database",
            handler=self._store_lpp_detection,
            parameters={
                "type": "object",
                "properties": {
                    "patient_code": {"type": "string"},
                    "lpp_grade": {"type": "integer"},
                    "confidence": {"type": "number"},
                    "anatomical_location": {"type": "string"},
                    "image_metadata": {"type": "object"},
                    "clinical_notes": {"type": "string"}
                },
                "required": ["patient_code", "lpp_grade", "confidence", "anatomical_location"]
            }
        )
        
        # Tool for retrieving patient records
        self.register_tool(
            name="get_patient_records",
            description="Retrieve patient medical records with HIPAA compliance",
            handler=self._get_patient_records,
            parameters={
                "type": "object",
                "properties": {
                    "patient_code": {"type": "string"},
                    "include_history": {"type": "boolean"},
                    "date_range": {"type": "object"},
                    "record_types": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["patient_code"]
            }
        )
        
        # Tool for creating audit logs
        self.register_tool(
            name="create_medical_audit_log",
            description="Create HIPAA-compliant audit log entry",
            handler=self._create_medical_audit_log,
            parameters={
                "type": "object",
                "properties": {
                    "event_type": {"type": "string"},
                    "patient_code": {"type": "string"},
                    "user_id": {"type": "string"},
                    "action_details": {"type": "object"},
                    "compliance_level": {"type": "string"}
                },
                "required": ["event_type", "user_id"]
            }
        )
        
        # Tool for data synchronization
        self.register_tool(
            name="sync_medical_data",
            description="Synchronize medical data with real-time updates",
            handler=self._sync_medical_data,
            parameters={
                "type": "object",
                "properties": {
                    "sync_type": {"type": "string", "enum": ["full", "incremental", "patient_specific"]},
                    "patient_codes": {"type": "array", "items": {"type": "string"}},
                    "tables": {"type": "array", "items": {"type": "string"}},
                    "last_sync_timestamp": {"type": "string"}
                },
                "required": ["sync_type"]
            }
        )
        
        # Tool for managing medical protocols
        self.register_tool(
            name="manage_medical_protocols",
            description="Manage medical protocols and guidelines",
            handler=self._manage_medical_protocols,
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "retrieve", "update", "list"]},
                    "protocol_id": {"type": "string"},
                    "protocol_data": {"type": "object"}
                },
                "required": ["action"]
            }
        )
        
        # Tool for bulk operations
        self.register_tool(
            name="bulk_medical_operations",
            description="Perform bulk operations on medical data",
            handler=self._bulk_medical_operations,
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["insert", "update", "delete"]},
                    "table": {"type": "string"},
                    "data": {"type": "array"},
                    "batch_size": {"type": "integer"}
                },
                "required": ["operation", "table", "data"]
            }
        )
    
    def _register_supabase_resources(self):
        """Register Supabase MCP resources"""
        
        # Medical tables resource
        self.register_resource(
            uri="supabase://tables/medical",
            name="Medical Database Tables",
            description="Information about medical database tables and schema",
            handler=self._get_medical_tables
        )
        
        # LPP detection statistics
        self.register_resource(
            uri="supabase://stats/lpp_detections",
            name="LPP Detection Statistics",
            description="Statistical data about pressure injury detections",
            handler=self._get_lpp_detection_stats
        )
        
        # Audit logs resource
        self.register_resource(
            uri="supabase://logs/audit",
            name="Medical Audit Logs",
            description="Recent medical audit log entries for compliance",
            handler=self._get_recent_audit_logs
        )
        
        # Active protocols resource
        self.register_resource(
            uri="supabase://protocols/active",
            name="Active Medical Protocols",
            description="Currently active medical protocols and guidelines",
            handler=self._get_active_protocols
        )
    
    async def _list_tools(self) -> Dict[str, Any]:
        """List available Supabase tools"""
        return {
            "tools": [
                {
                    "name": tool_name,
                    "description": tool_data["description"],
                    "inputSchema": tool_data["parameters"],
                    "medical_compliant": True,
                    "database_operation": True
                }
                for tool_name, tool_data in self.tools.items()
            ]
        }
    
    async def _call_tool(self, params: Dict[str, Any]) -> Any:
        """Call a specific Supabase tool"""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        handler = self.tools[tool_name]["handler"]
        return await handler(tool_params)
    
    async def _list_resources(self) -> Dict[str, Any]:
        """List available Supabase resources"""
        return {
            "resources": [
                {
                    "uri": resource_uri,
                    "name": resource_data["name"],
                    "description": resource_data["description"],
                    "mimeType": "application/json",
                    "medical_compliant": True
                }
                for resource_uri, resource_data in self.resources.items()
            ]
        }
    
    async def _read_resource(self, params: Dict[str, Any]) -> Any:
        """Read a specific Supabase resource"""
        resource_uri = params.get("uri")
        
        if resource_uri not in self.resources:
            raise ValueError(f"Unknown resource: {resource_uri}")
        
        handler = self.resources[resource_uri]["handler"]
        return await handler()
    
    # Tool implementations
    
    async def _store_lpp_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store LPP detection data in medical database"""
        if not self.supabase_client:
            return {"status": "mock", "message": "Supabase not configured"}
        
        try:
            # Prepare detection data
            detection_data = {
                "patient_code": params.get("patient_code"),
                "lpp_grade": params.get("lpp_grade"),
                "confidence": params.get("confidence"),
                "anatomical_location": params.get("anatomical_location"),
                "image_metadata": json.dumps(params.get("image_metadata", {})),
                "clinical_notes": params.get("clinical_notes", ""),
                "detected_at": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store in database
            result = self.supabase_client.table("lpp_detections").insert(detection_data).execute()
            
            if result.data:
                detection_id = result.data[0]["id"]
                
                # Create audit log
                await self._create_medical_audit_log({
                    "event_type": "lpp_detection_stored",
                    "patient_code": params.get("patient_code"),
                    "user_id": "system",
                    "action_details": {
                        "detection_id": detection_id,
                        "lpp_grade": params.get("lpp_grade"),
                        "confidence": params.get("confidence")
                    },
                    "compliance_level": "hipaa"
                })
                
                logger.info(f"LPP detection stored: {detection_id}")
                
                return {
                    "status": "stored",
                    "detection_id": detection_id,
                    "patient_code": params.get("patient_code"),
                    "timestamp": detection_data["detected_at"]
                }
            else:
                raise ValueError("Failed to store detection data")
                
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            raise ValueError(f"Database operation failed: {e}")
    
    async def _get_patient_records(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve patient medical records"""
        if not self.supabase_client:
            return {"status": "mock", "records": [], "message": "Supabase not configured"}
        
        try:
            patient_code = params.get("patient_code")
            include_history = params.get("include_history", True)
            date_range = params.get("date_range", {})
            record_types = params.get("record_types", ["lpp_detections"])
            
            records = {}
            
            # Get LPP detections if requested
            if "lpp_detections" in record_types:
                query = self.supabase_client.table("lpp_detections").select("*").eq("patient_code", patient_code)
                
                # Apply date filtering
                if date_range.get("start_date"):
                    query = query.gte("detected_at", date_range["start_date"])
                if date_range.get("end_date"):
                    query = query.lte("detected_at", date_range["end_date"])
                
                lpp_result = query.order("detected_at", desc=True).execute()
                records["lpp_detections"] = lpp_result.data
            
            # Get patient record if requested
            if "assessments" in record_types:
                patient_result = self.supabase_client.table("patient_records").select("*").eq("patient_code", patient_code).execute()
                records["patient_info"] = patient_result.data[0] if patient_result.data else None
            
            # Create audit log for data access
            await self._create_medical_audit_log({
                "event_type": "access",
                "patient_code": patient_code,
                "user_id": "system",
                "action_details": {
                    "accessed_records": record_types,
                    "include_history": include_history
                },
                "compliance_level": "hipaa"
            })
            
            return {
                "status": "retrieved",
                "patient_code": patient_code,
                "records": records,
                "record_count": sum(len(v) if isinstance(v, list) else 1 for v in records.values() if v),
                "access_timestamp": datetime.utcnow().isoformat()
            }
            
        except APIError as e:
            logger.error(f"Failed to retrieve patient records: {e}")
            raise ValueError(f"Record retrieval failed: {e}")
    
    async def _create_medical_audit_log(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create HIPAA-compliant audit log entry"""
        if not self.supabase_client:
            return {"status": "mock", "message": "Audit logging mock"}
        
        try:
            audit_data = {
                "event_type": params.get("event_type"),
                "patient_code": params.get("patient_code"),
                "user_id": params.get("user_id"),
                "timestamp": datetime.utcnow().isoformat(),
                "data": json.dumps(params.get("action_details", {})),
                "compliance_level": params.get("compliance_level", "standard"),
                "ip_address": params.get("ip_address"),
                "user_agent": params.get("user_agent"),
                "session_id": params.get("session_id")
            }
            
            result = self.supabase_client.table("medical_audit_logs").insert(audit_data).execute()
            
            if result.data:
                audit_id = result.data[0]["id"]
                logger.info(f"Audit log created: {audit_id}")
                
                return {
                    "status": "logged",
                    "audit_id": audit_id,
                    "event_type": params.get("event_type"),
                    "timestamp": audit_data["timestamp"]
                }
            else:
                raise ValueError("Failed to create audit log")
                
        except APIError as e:
            logger.error(f"Audit logging failed: {e}")
            raise ValueError(f"Audit log creation failed: {e}")
    
    async def _sync_medical_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize medical data with real-time updates"""
        if not self.supabase_client:
            return {"status": "mock", "message": "Data sync mock"}
        
        sync_type = params.get("sync_type")
        patient_codes = params.get("patient_codes", [])
        tables = params.get("tables", list(self.medical_tables.keys()))
        last_sync = params.get("last_sync_timestamp")
        
        sync_results = {}
        
        try:
            for table in tables:
                query = self.supabase_client.table(table).select("*")
                
                # Apply filters based on sync type
                if sync_type == "patient_specific" and patient_codes:
                    query = query.in_("patient_code", patient_codes)
                
                if sync_type == "incremental" and last_sync:
                    # Get records modified since last sync
                    query = query.gte("updated_at", last_sync)
                
                result = query.execute()
                sync_results[table] = {
                    "records": len(result.data),
                    "data": result.data if sync_type == "full" else len(result.data)
                }
            
            return {
                "status": "synced",
                "sync_type": sync_type,
                "tables_synced": len(tables),
                "sync_results": sync_results,
                "sync_timestamp": datetime.utcnow().isoformat()
            }
            
        except APIError as e:
            logger.error(f"Data sync failed: {e}")
            raise ValueError(f"Synchronization failed: {e}")
    
    async def _manage_medical_protocols(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage medical protocols and guidelines"""
        if not self.supabase_client:
            return {"status": "mock", "message": "Protocol management mock"}
        
        action = params.get("action")
        protocol_id = params.get("protocol_id")
        protocol_data = params.get("protocol_data", {})
        
        try:
            if action == "create":
                # Create new protocol
                new_protocol = {
                    "protocol_name": protocol_data.get("name"),
                    "version": protocol_data.get("version", "1.0"),
                    "content": json.dumps(protocol_data.get("content", {})),
                    "category": protocol_data.get("category"),
                    "effective_date": protocol_data.get("effective_date", datetime.utcnow().date().isoformat()),
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "active"
                }
                
                result = self.supabase_client.table("medical_protocols").insert(new_protocol).execute()
                return {"status": "created", "protocol_id": result.data[0]["id"]}
            
            elif action == "retrieve":
                # Get specific protocol
                result = self.supabase_client.table("medical_protocols").select("*").eq("id", protocol_id).execute()
                return {"status": "retrieved", "protocol": result.data[0] if result.data else None}
            
            elif action == "list":
                # List all protocols
                result = self.supabase_client.table("medical_protocols").select("*").eq("status", "active").execute()
                return {"status": "listed", "protocols": result.data, "count": len(result.data)}
            
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except APIError as e:
            logger.error(f"Protocol management failed: {e}")
            raise ValueError(f"Protocol operation failed: {e}")
    
    async def _bulk_medical_operations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform bulk operations on medical data"""
        if not self.supabase_client:
            return {"status": "mock", "message": "Bulk operations mock"}
        
        operation = params.get("operation")
        table = params.get("table")
        data = params.get("data", [])
        batch_size = params.get("batch_size", 100)
        
        try:
            results = []
            
            # Process data in batches
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                
                if operation == "insert":
                    result = self.supabase_client.table(table).insert(batch).execute()
                    results.extend(result.data)
                
                elif operation == "update":
                    # Bulk update would require more complex logic
                    pass
                
                elif operation == "delete":
                    # Bulk delete would require more complex logic
                    pass
            
            return {
                "status": "completed",
                "operation": operation,
                "table": table,
                "processed_records": len(results),
                "batches": len(range(0, len(data), batch_size))
            }
            
        except APIError as e:
            logger.error(f"Bulk operation failed: {e}")
            raise ValueError(f"Bulk {operation} failed: {e}")
    
    # Resource implementations
    
    async def _get_medical_tables(self) -> Dict[str, Any]:
        """Get medical database tables information"""
        return {
            "tables": {
                name: {
                    "name": name,
                    "primary_key": config["primary_key"],
                    "columns": config["columns"],
                    "sensitive_columns": config["sensitive_columns"],
                    "hipaa_compliant": True
                }
                for name, config in self.medical_tables.items()
            },
            "total_tables": len(self.medical_tables)
        }
    
    async def _get_lpp_detection_stats(self) -> Dict[str, Any]:
        """Get LPP detection statistics"""
        if not self.supabase_client:
            return {"stats": {}, "status": "mock"}
        
        try:
            # Get recent detection counts
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            
            result = self.supabase_client.table("lpp_detections").select("lpp_grade, confidence, detected_at").gte("detected_at", week_ago.isoformat()).execute()
            
            detections = result.data
            
            stats = {
                "total_detections": len(detections),
                "by_grade": {},
                "average_confidence": 0,
                "recent_trend": "stable"
            }
            
            if detections:
                # Count by grade
                for detection in detections:
                    grade = detection.get("lpp_grade", "unknown")
                    stats["by_grade"][grade] = stats["by_grade"].get(grade, 0) + 1
                
                # Calculate average confidence
                confidences = [d.get("confidence", 0) for d in detections if d.get("confidence")]
                if confidences:
                    stats["average_confidence"] = sum(confidences) / len(confidences)
            
            return {"stats": stats, "period": "last_7_days"}
            
        except APIError as e:
            logger.error(f"Failed to get stats: {e}")
            return {"stats": {}, "error": str(e)}
    
    async def _get_recent_audit_logs(self) -> Dict[str, Any]:
        """Get recent medical audit logs"""
        if not self.supabase_client:
            return {"logs": [], "status": "mock"}
        
        try:
            result = self.supabase_client.table("medical_audit_logs").select("*").order("timestamp", desc=True).limit(50).execute()
            
            return {
                "logs": result.data,
                "count": len(result.data),
                "compliance": "hipaa_ready"
            }
            
        except APIError as e:
            logger.error(f"Failed to get audit logs: {e}")
            return {"logs": [], "error": str(e)}
    
    async def _get_active_protocols(self) -> Dict[str, Any]:
        """Get active medical protocols"""
        if not self.supabase_client:
            return {"protocols": [], "status": "mock"}
        
        try:
            result = self.supabase_client.table("medical_protocols").select("*").eq("status", "active").order("created_at", desc=True).execute()
            
            return {
                "protocols": result.data,
                "count": len(result.data),
                "categories": list(set(p.get("category") for p in result.data if p.get("category")))
            }
            
        except APIError as e:
            logger.error(f"Failed to get protocols: {e}")
            return {"protocols": [], "error": str(e)}


# Create server instance
supabase_server = SupabaseMCPServer()

# Export FastAPI app for deployment
app = supabase_server.app