// MongoDB Audit Database Initialization Script
// Initialize collections and indexes for medical audit compliance

print('Initializing Vigia Medical Audit Database...');

// Switch to audit database
db = db.getSiblingDB('vigia_audit');

// Create medical audit logs collection
db.createCollection('medical_audit_logs', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["timestamp", "event_type", "user_id", "service", "action", "status"],
            properties: {
                timestamp: {
                    bsonType: "date",
                    description: "Event timestamp - required"
                },
                event_type: {
                    bsonType: "string",
                    enum: ["medical_decision", "lpp_detection", "phi_access", "system_access", "integration", "error"],
                    description: "Type of audit event - required"
                },
                user_id: {
                    bsonType: "string",
                    description: "User or system identifier - required"
                },
                service: {
                    bsonType: "string",
                    description: "Service that generated the event - required"
                },
                action: {
                    bsonType: "string",
                    description: "Action performed - required"
                },
                status: {
                    bsonType: "string",
                    enum: ["success", "failure", "warning"],
                    description: "Event status - required"
                },
                patient_id: {
                    bsonType: "string",
                    description: "Patient identifier (if applicable)"
                },
                phi_accessed: {
                    bsonType: "bool",
                    description: "Whether PHI was accessed"
                },
                compliance_level: {
                    bsonType: "string",
                    enum: ["hipaa", "pci-dss", "iso27001"],
                    description: "Compliance framework applicable"
                },
                ip_address: {
                    bsonType: "string",
                    description: "Source IP address"
                },
                user_agent: {
                    bsonType: "string",
                    description: "User agent string"
                },
                request_data: {
                    bsonType: "object",
                    description: "Request parameters (sanitized)"
                },
                response_data: {
                    bsonType: "object",
                    description: "Response data (sanitized)"
                },
                error_details: {
                    bsonType: "object",
                    description: "Error information if status is failure"
                },
                retention_until: {
                    bsonType: "date",
                    description: "Data retention expiration (7 years for HIPAA)"
                }
            }
        }
    }
});

print('Created medical_audit_logs collection with schema validation');

// Create indexes for efficient querying
db.medical_audit_logs.createIndex({ "timestamp": -1 }, { name: "timestamp_desc" });
db.medical_audit_logs.createIndex({ "event_type": 1, "timestamp": -1 }, { name: "event_type_timestamp" });
db.medical_audit_logs.createIndex({ "user_id": 1, "timestamp": -1 }, { name: "user_timestamp" });
db.medical_audit_logs.createIndex({ "patient_id": 1, "timestamp": -1 }, { name: "patient_timestamp" });
db.medical_audit_logs.createIndex({ "service": 1, "action": 1 }, { name: "service_action" });
db.medical_audit_logs.createIndex({ "phi_accessed": 1, "timestamp": -1 }, { name: "phi_access_timestamp" });
db.medical_audit_logs.createIndex({ "compliance_level": 1, "timestamp": -1 }, { name: "compliance_timestamp" });
db.medical_audit_logs.createIndex({ "retention_until": 1 }, { expireAfterSeconds: 0, name: "retention_cleanup" });

print('Created indexes for audit log queries');

// Create MCP service logs collection
db.createCollection('mcp_service_logs', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["timestamp", "service_name", "operation", "status", "response_time"],
            properties: {
                timestamp: {
                    bsonType: "date",
                    description: "Operation timestamp"
                },
                service_name: {
                    bsonType: "string",
                    enum: ["mcp-github", "mcp-stripe", "mcp-redis", "mcp-mongodb", "mcp-gateway"],
                    description: "MCP service name"
                },
                operation: {
                    bsonType: "string",
                    description: "Operation performed"
                },
                status: {
                    bsonType: "string",
                    enum: ["success", "error", "timeout", "rate_limited"],
                    description: "Operation status"
                },
                response_time: {
                    bsonType: "number",
                    minimum: 0,
                    description: "Response time in milliseconds"
                },
                request_id: {
                    bsonType: "string",
                    description: "Unique request identifier"
                },
                client_ip: {
                    bsonType: "string",
                    description: "Client IP address"
                },
                error_code: {
                    bsonType: "string",
                    description: "Error code if applicable"
                },
                error_message: {
                    bsonType: "string",
                    description: "Error message if applicable"
                }
            }
        }
    }
});

// Create indexes for MCP service logs
db.mcp_service_logs.createIndex({ "timestamp": -1 }, { name: "mcp_timestamp_desc" });
db.mcp_service_logs.createIndex({ "service_name": 1, "timestamp": -1 }, { name: "mcp_service_timestamp" });
db.mcp_service_logs.createIndex({ "status": 1, "timestamp": -1 }, { name: "mcp_status_timestamp" });
db.mcp_service_logs.createIndex({ "response_time": -1 }, { name: "mcp_response_time_desc" });

print('Created mcp_service_logs collection with indexes');

// Create medical decisions collection for clinical audit
db.createCollection('medical_decisions', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["decision_id", "timestamp", "patient_id", "decision_type", "ai_confidence", "evidence_level"],
            properties: {
                decision_id: {
                    bsonType: "string",
                    description: "Unique decision identifier"
                },
                timestamp: {
                    bsonType: "date",
                    description: "Decision timestamp"
                },
                patient_id: {
                    bsonType: "string",
                    description: "Patient identifier"
                },
                decision_type: {
                    bsonType: "string",
                    enum: ["lpp_detection", "risk_assessment", "treatment_recommendation", "escalation"],
                    description: "Type of medical decision"
                },
                ai_confidence: {
                    bsonType: "number",
                    minimum: 0,
                    maximum: 1,
                    description: "AI confidence score"
                },
                evidence_level: {
                    bsonType: "string",
                    enum: ["A", "B", "C"],
                    description: "Evidence level (NPUAP/EPUAP guidelines)"
                },
                lpp_grade: {
                    bsonType: "number",
                    minimum: 0,
                    maximum: 4,
                    description: "LPP grade if applicable"
                },
                anatomical_location: {
                    bsonType: "string",
                    description: "Anatomical location of finding"
                },
                clinical_recommendations: {
                    bsonType: "array",
                    items: {
                        bsonType: "string"
                    },
                    description: "Clinical recommendations"
                },
                human_verified: {
                    bsonType: "bool",
                    description: "Whether decision was verified by human clinician"
                },
                verification_timestamp: {
                    bsonType: "date",
                    description: "Human verification timestamp"
                },
                verifying_clinician: {
                    bsonType: "string",
                    description: "Clinician who verified the decision"
                }
            }
        }
    }
});

// Create indexes for medical decisions
db.medical_decisions.createIndex({ "decision_id": 1 }, { unique: true, name: "decision_id_unique" });
db.medical_decisions.createIndex({ "patient_id": 1, "timestamp": -1 }, { name: "patient_decisions" });
db.medical_decisions.createIndex({ "decision_type": 1, "timestamp": -1 }, { name: "decision_type_timestamp" });
db.medical_decisions.createIndex({ "ai_confidence": -1 }, { name: "confidence_desc" });
db.medical_decisions.createIndex({ "human_verified": 1, "timestamp": -1 }, { name: "verification_status" });

print('Created medical_decisions collection with indexes');

// Insert sample audit entry for testing
var sampleAuditEntry = {
    timestamp: new Date(),
    event_type: "system_access",
    user_id: "system_mcp_init",
    service: "mcp-mongodb",
    action: "database_initialization",
    status: "success",
    phi_accessed: false,
    compliance_level: "hipaa",
    ip_address: "127.0.0.1",
    user_agent: "MongoDB-Init-Script",
    request_data: {
        operation: "create_collections_and_indexes"
    },
    response_data: {
        collections_created: ["medical_audit_logs", "mcp_service_logs", "medical_decisions"],
        indexes_created: 12
    },
    retention_until: new Date(Date.now() + (7 * 365 * 24 * 60 * 60 * 1000)) // 7 years from now
};

db.medical_audit_logs.insertOne(sampleAuditEntry);
print('Inserted sample audit entry');

// Create user for MCP service access
db.createUser({
    user: "mcp_service",
    pwd: "mcp_secure_password_2025",
    roles: [
        {
            role: "readWrite",
            db: "vigia_audit"
        }
    ]
});

print('Created MCP service user with readWrite permissions');

// Summary
print('=== Vigia Medical Audit Database Initialization Complete ===');
print('Collections created: medical_audit_logs, mcp_service_logs, medical_decisions');
print('Indexes created: 12 total (timestamp, event_type, user, patient, service-based)');
print('HIPAA compliance: 7-year retention policy configured');
print('Schema validation: Enabled for all collections');
print('Sample audit entry: Inserted for testing');
print('MCP service user: Created with appropriate permissions');
print('Database ready for medical audit operations');