# Vigia Documentation

Medical-grade pressure injury detection system with clean ADK architecture.

## Essential Documentation

### 🏥 Medical & Clinical
- [NPUAP/EPUAP Guidelines](medical/NPUAP_EPUAP_CLINICAL_DECISIONS.md) - Evidence-based medical decisions
- [MINSAL Integration](medical/minsal-integration.md) - Chilean regulatory compliance
- [Medical Evidence Report](medical/MEDICAL_EVIDENCE_IMPLEMENTATION_REPORT.md) - Implementation details

### 🚀 Deployment & Operations
- [Hospital Deployment](deployment/HOSPITAL_DEPLOYMENT.md) - Docker production setup
- [Render Deployment](deployment/render-deployment.md) - Cloud deployment
- [Backup Guide](deployment/BACKUP_GUIDE.md) - Data protection

### ⚙️ Setup & Configuration
- [MedGemma Local AI](setup/MEDGEMMA_LOCAL_SETUP.md) - Local medical AI setup
- [Redis Integration](setup/REDIS_MEDGEMMA_INTEGRATION.md) - Vector search configuration
- [Credentials Management](setup/CREDENTIALS_MANAGEMENT.md) - Security setup
- [MCP Setup](setup/MCP_SETUP.md) - Model Context Protocol

### 🔧 Module Documentation
- [Database](db/) - Supabase integration and policies
- [CV Pipeline](cv_pipeline/) - YOLOv5 medical image processing
- [Messaging](messaging/) - WhatsApp/Slack integration
- [CLI Tools](cli/) - Command-line utilities

## Project Status

✅ **Production Ready** - Clean ADK architecture with medical compliance
- Real medical detection with 2,088+ validated images
- Evidence-based decisions with NPUAP/EPUAP + MINSAL
- HIPAA/ISO 13485/SOC2 compliance ready