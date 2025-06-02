# CLAUDE.md - Vigia Project Instructions

## Project Overview
Vigia is a medical detection system for pressure injuries (LPP - Lesiones Por Presión) that uses computer vision and AI to help healthcare providers identify and track patient conditions. The system integrates with messaging platforms (WhatsApp, Slack) and features a custom webhook system for external integrations.

## Key Project Context

### Architecture
- **Main Detection Pipeline**: `vigia_detect/` - Core CV and detection logic
- **Messaging Integration**: WhatsApp bot and Slack notifications
- **Database**: Supabase (shared with autonomos-agent project)
- **Redis**: Caching layer for medical protocols and embeddings
- **Webhook System**: Custom webhook client/server for external integrations

### Important Commands
```bash
# Run tests
npm run test

# Lint code
npm run lint

# Type checking
npm run typecheck

# Start WhatsApp server
./start_whatsapp_server.sh

# Start Slack server
./scripts/start_slack_server.sh

# Process images with webhook notifications
python vigia_detect/cli/process_images_refactored.py --webhook
```

### API Keys and Services
- Uses Anthropic Claude API for AI capabilities
- Supabase instance: autonomos-agent project
- Twilio for WhatsApp integration
- Slack API for notifications

### Webhook System
The project includes a custom webhook system to send detection results to external services:

1. **Configuration** (via environment variables):
   - `WEBHOOK_ENABLED`: Enable/disable webhooks globally
   - `WEBHOOK_URL`: Target webhook endpoint
   - `WEBHOOK_API_KEY`: Optional authentication token
   - `WEBHOOK_TIMEOUT`: Request timeout (default: 30s)
   - `WEBHOOK_RETRY_COUNT`: Number of retry attempts (default: 3)

2. **CLI Usage**:
   ```bash
   # Send results via webhook
   python process_images_refactored.py --webhook --patient-code CD-2025-001
   
   # Override webhook URL
   python process_images_refactored.py --webhook --webhook-url https://api.example.com/webhook
   ```

3. **Webhook Events**:
   - `detection.completed`: When image processing completes
   - `detection.failed`: When processing fails
   - `patient.updated`: When patient data changes
   - `protocol.triggered`: When medical protocol is activated

### Code Style Guidelines
- Use existing patterns from the codebase
- Follow the modular architecture in `vigia_detect/`
- Maintain separation between core logic, messaging, and UI layers
- Use type hints in Python code
- Follow existing import patterns (vigia_detect, not lpp_detect)

### Testing Requirements
- Always run tests after making changes
- Use pytest for Python tests
- Mock external services (Twilio, Slack, Supabase) in tests
- Check `tests/` directories in each module

### Security Considerations
- Never commit API keys or secrets
- Use environment variables for configuration
- Medical data is sensitive - ensure proper handling
- Follow HIPAA-like practices for patient information

### Module-Specific Notes

#### CV Pipeline (`vigia_detect/cv_pipeline/`)
- Handles image preprocessing and detection
- Uses YOLO for object detection
- Outputs detection results with confidence scores

#### Messaging (`vigia_detect/messaging/`)
- WhatsApp: Handles incoming images and sends results
- Slack: Sends formatted notifications with detection results
- Templates in `templates/` for consistent messaging

#### Webhook System (`vigia_detect/webhook/`)
- Client: Async/sync webhook sender with retry logic
- Server: FastAPI-based webhook receiver
- Models: Structured event payloads for medical data
- Full authentication support with Bearer tokens

#### Redis Layer (`vigia_detect/redis_layer/`)
- Caches medical protocols and embeddings
- Vector search for similar cases
- Two-phase implementation (Phase 1: basic cache, Phase 2: vectors)

#### Database (`vigia_detect/db/`)
- Supabase client for data persistence
- Stores detection history and patient records
- Row-level security policies for data protection

### Development Workflow
1. Make changes in feature branches
2. Run tests locally before committing
3. Use meaningful commit messages
4. Update documentation if adding new features
5. Test integrations (WhatsApp/Slack/Webhooks) manually when modifying messaging

### Common Tasks
- **Adding a new medical protocol**: Update Redis cache and protocol indexer
- **Modifying detection logic**: Work in `cv_pipeline/detector.py`
- **Updating message templates**: Edit files in `messaging/templates/`
- **Adding new Slack blocks**: Modify `core/slack_templates.py`
- **Creating webhook handlers**: Add handlers in webhook server or implement receiver

### Current Focus Areas
- Improving detection accuracy for pressure injuries
- Building custom medical UI and agent system
- Implementing patient history and memory features
- Expanding webhook integrations for hospital systems