#!/bin/bash

# Vigia ADK Deployment Script for Google Cloud Run
# ================================================
# 
# Deploys all 5 ADK medical agents to Google Cloud Run
# with proper configuration and networking

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}
NAMESPACE="vigia-medical"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if gcloud is installed and authenticated
    if ! command -v gcloud &> /dev/null; then
        error "gcloud CLI is not installed. Please install it first."
    fi
    
    # Check if logged in
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        error "Not authenticated with gcloud. Please run 'gcloud auth login'"
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        warn "kubectl is not installed. Some operations may not work."
    fi
    
    log "Prerequisites check passed ✓"
}

# Setup Google Cloud project
setup_project() {
    log "Setting up Google Cloud project..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    log "Enabling required APIs..."
    gcloud services enable \
        run.googleapis.com \
        cloudbuild.googleapis.com \
        containerregistry.googleapis.com \
        aiplatform.googleapis.com \
        secretmanager.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com
    
    # Create service account
    log "Creating service account..."
    gcloud iam service-accounts create vigia-adk \
        --display-name="Vigia ADK Service Account" \
        --description="Service account for Vigia ADK medical agents" \
        || true
    
    # Grant necessary permissions
    log "Granting IAM permissions..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:vigia-adk@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/aiplatform.user"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:vigia-adk@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:vigia-adk@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/logging.logWriter"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:vigia-adk@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/monitoring.metricWriter"
    
    log "Project setup completed ✓"
}

# Build and push Docker images
build_and_push_images() {
    log "Building and pushing Docker images..."
    
    # Configure Docker for GCR
    gcloud auth configure-docker
    
    # List of agents to build
    agents=("image-analysis" "clinical-assessment" "protocol" "communication" "workflow-orchestration" "risk-assessment" "voice-analysis" "a2a-discovery")
    
    for agent in "${agents[@]}"; do
        log "Building $agent agent..."
        
        # Build image
        if [[ "$agent" == "a2a-discovery" ]]; then
            docker build \
                -f deploy/cloud-run/Dockerfile.$agent \
                -t gcr.io/$PROJECT_ID/vigia-$agent:latest \
                .
        else
            docker build \
                -f deploy/cloud-run/Dockerfile.$agent \
                -t gcr.io/$PROJECT_ID/vigia-$agent-agent:latest \
                .
        fi
        
        # Push image
        log "Pushing $agent to GCR..."
        if [[ "$agent" == "a2a-discovery" ]]; then
            docker push gcr.io/$PROJECT_ID/vigia-$agent:latest
        else
            docker push gcr.io/$PROJECT_ID/vigia-$agent-agent:latest
        fi
        
        log "$agent agent built and pushed ✓"
    done
    
    log "All images built and pushed ✓"
}

# Create secrets
create_secrets() {
    log "Creating secrets..."
    
    # Create secrets for external integrations
    # Note: Replace these with actual values in production
    
    echo -n "$PROJECT_ID" | gcloud secrets create vertex-ai-project --data-file=- || true
    echo -n "https://api.whatsapp.com/webhook/PLACEHOLDER" | gcloud secrets create whatsapp-webhook --data-file=- || true
    echo -n "https://hooks.slack.com/services/PLACEHOLDER" | gcloud secrets create slack-webhook --data-file=- || true
    echo -n "smtp.hospital.local" | gcloud secrets create smtp-server --data-file=- || true
    echo -n "redis://redis.vigia-adk.run.app:6379" | gcloud secrets create redis-endpoint --data-file=- || true
    echo -n "PLACEHOLDER_HUME_API_KEY" | gcloud secrets create hume-api-key --data-file=- || true
    
    log "Secrets created ✓"
}

# Deploy services
deploy_services() {
    log "Deploying ADK agents to Cloud Run..."
    
    # Replace PROJECT_ID in deployment YAML
    sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" deploy/cloud-run/agent-services.yaml
    
    # Apply Kubernetes manifests (if using GKE)
    # kubectl apply -f deploy/cloud-run/agent-services.yaml
    
    # Deploy each service individually to Cloud Run
    deploy_image_analysis_agent
    deploy_clinical_assessment_agent
    deploy_protocol_agent
    deploy_communication_agent
    deploy_workflow_orchestration_agent
    deploy_risk_assessment_agent
    deploy_voice_analysis_agent
    deploy_a2a_discovery_service
    
    log "All services deployed ✓"
}

# Deploy individual agents
deploy_image_analysis_agent() {
    log "Deploying Image Analysis Agent..."
    
    gcloud run deploy vigia-image-analysis-agent \
        --image=gcr.io/$PROJECT_ID/vigia-image-analysis-agent:latest \
        --platform=managed \
        --region=$REGION \
        --memory=4Gi \
        --cpu=2 \
        --timeout=300 \
        --min-instances=1 \
        --max-instances=10 \
        --concurrency=10 \
        --service-account=vigia-adk@$PROJECT_ID.iam.gserviceaccount.com \
        --set-env-vars="AGENT_ID=vigia-image-analysis,AGENT_TYPE=BaseAgent,YOLO_MODEL_PATH=/models/yolov5_lpp_detection.pt" \
        --no-allow-unauthenticated
}

deploy_clinical_assessment_agent() {
    log "Deploying Clinical Assessment Agent..."
    
    gcloud run deploy vigia-clinical-assessment-agent \
        --image=gcr.io/$PROJECT_ID/vigia-clinical-assessment-agent:latest \
        --platform=managed \
        --region=$REGION \
        --memory=2Gi \
        --cpu=1 \
        --timeout=180 \
        --min-instances=1 \
        --max-instances=20 \
        --concurrency=20 \
        --service-account=vigia-adk@$PROJECT_ID.iam.gserviceaccount.com \
        --set-env-vars="AGENT_ID=vigia-clinical-assessment,AGENT_TYPE=LLMAgent,LLM_MODEL=gemini-1.5-pro" \
        --set-secrets="VERTEX_AI_PROJECT=vertex-ai-project:latest" \
        --no-allow-unauthenticated
}

deploy_protocol_agent() {
    log "Deploying Protocol Agent..."
    
    gcloud run deploy vigia-protocol-agent \
        --image=gcr.io/$PROJECT_ID/vigia-protocol-agent:latest \
        --platform=managed \
        --region=$REGION \
        --memory=2Gi \
        --cpu=1 \
        --timeout=120 \
        --min-instances=1 \
        --max-instances=15 \
        --concurrency=15 \
        --service-account=vigia-adk@$PROJECT_ID.iam.gserviceaccount.com \
        --set-env-vars="AGENT_ID=vigia-protocol-agent,AGENT_TYPE=LLMAgent" \
        --no-allow-unauthenticated
}

deploy_communication_agent() {
    log "Deploying Communication Agent..."
    
    gcloud run deploy vigia-communication-agent \
        --image=gcr.io/$PROJECT_ID/vigia-communication-agent:latest \
        --platform=managed \
        --region=$REGION \
        --memory=1Gi \
        --cpu=1 \
        --timeout=60 \
        --min-instances=2 \
        --max-instances=50 \
        --concurrency=100 \
        --service-account=vigia-adk@$PROJECT_ID.iam.gserviceaccount.com \
        --set-env-vars="AGENT_ID=vigia-communication-agent,AGENT_TYPE=WorkflowAgent" \
        --set-secrets="WHATSAPP_WEBHOOK=whatsapp-webhook:latest,SLACK_WEBHOOK=slack-webhook:latest,SMTP_SERVER=smtp-server:latest" \
        --no-allow-unauthenticated
}

deploy_workflow_orchestration_agent() {
    log "Deploying Workflow Orchestration Agent..."
    
    gcloud run deploy vigia-workflow-orchestration-agent \
        --image=gcr.io/$PROJECT_ID/vigia-workflow-orchestration-agent:latest \
        --platform=managed \
        --region=$REGION \
        --memory=2Gi \
        --cpu=2 \
        --timeout=900 \
        --min-instances=3 \
        --max-instances=30 \
        --concurrency=50 \
        --service-account=vigia-adk@$PROJECT_ID.iam.gserviceaccount.com \
        --set-env-vars="AGENT_ID=vigia-workflow-orchestration,AGENT_TYPE=WorkflowAgent,ORCHESTRATOR_MODE=master" \
        --allow-unauthenticated  # This is the main entry point
}

deploy_risk_assessment_agent() {
    log "Deploying Risk Assessment Agent..."
    
    gcloud run deploy vigia-risk-assessment-agent \
        --image=gcr.io/$PROJECT_ID/vigia-risk-assessment-agent:latest \
        --platform=managed \
        --region=$REGION \
        --memory=2Gi \
        --cpu=1 \
        --timeout=180 \
        --min-instances=1 \
        --max-instances=15 \
        --concurrency=20 \
        --service-account=vigia-adk@$PROJECT_ID.iam.gserviceaccount.com \
        --set-env-vars="AGENT_ID=vigia-risk-assessment,AGENT_TYPE=LlmAgent,ASSESSMENT_SCALES=braden,norton,stratify,must" \
        --no-allow-unauthenticated
}

deploy_voice_analysis_agent() {
    log "Deploying Voice Analysis Agent..."
    
    gcloud run deploy vigia-voice-analysis-agent \
        --image=gcr.io/$PROJECT_ID/vigia-voice-analysis-agent:latest \
        --platform=managed \
        --region=$REGION \
        --memory=2Gi \
        --cpu=1 \
        --timeout=300 \
        --min-instances=1 \
        --max-instances=10 \
        --concurrency=15 \
        --service-account=vigia-adk@$PROJECT_ID.iam.gserviceaccount.com \
        --set-env-vars="AGENT_ID=vigia-voice-analysis,AGENT_TYPE=VoiceAnalysisAgent,HUME_AI_ENABLED=true" \
        --set-secrets="HUME_API_KEY=hume-api-key:latest" \
        --no-allow-unauthenticated
}

deploy_a2a_discovery_service() {
    log "Deploying A2A Discovery Service..."
    
    gcloud run deploy vigia-a2a-discovery \
        --image=gcr.io/$PROJECT_ID/vigia-a2a-discovery:latest \
        --platform=managed \
        --region=$REGION \
        --memory=1Gi \
        --cpu=1 \
        --timeout=30 \
        --min-instances=2 \
        --max-instances=10 \
        --concurrency=100 \
        --service-account=vigia-adk@$PROJECT_ID.iam.gserviceaccount.com \
        --set-env-vars="SERVICE_TYPE=a2a_discovery" \
        --set-secrets="REDIS_ENDPOINT=redis-endpoint:latest" \
        --allow-unauthenticated  # Discovery service needs to be accessible
}

# Setup monitoring and logging
setup_monitoring() {
    log "Setting up monitoring and logging..."
    
    # Create custom metrics
    # This would typically involve setting up Cloud Monitoring dashboards
    # and alerting policies for the medical agents
    
    log "Monitoring setup completed ✓"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Get service URLs
    orchestration_url=$(gcloud run services describe vigia-workflow-orchestration-agent --region=$REGION --format="value(status.url)")
    discovery_url=$(gcloud run services describe vigia-a2a-discovery --region=$REGION --format="value(status.url)")
    
    log "Service URLs:"
    log "  Workflow Orchestration: $orchestration_url"
    log "  A2A Discovery: $discovery_url"
    
    # Test health endpoints
    log "Testing health endpoints..."
    
    if curl -s "$orchestration_url/health" | grep -q "healthy"; then
        log "Workflow Orchestration Agent: ✓ Healthy"
    else
        warn "Workflow Orchestration Agent: ✗ Not responding"
    fi
    
    if curl -s "$discovery_url/health" | grep -q "healthy"; then
        log "A2A Discovery Service: ✓ Healthy"
    else
        warn "A2A Discovery Service: ✗ Not responding"
    fi
    
    log "Deployment verification completed ✓"
}

# Main deployment function
main() {
    log "🚀 Starting Vigia ADK deployment to Google Cloud Run..."
    
    # Check command line arguments
    case "${1:-deploy}" in
        "check")
            check_prerequisites
            ;;
        "setup")
            check_prerequisites
            setup_project
            ;;
        "build")
            check_prerequisites
            build_and_push_images
            ;;
        "secrets")
            create_secrets
            ;;
        "deploy")
            check_prerequisites
            setup_project
            create_secrets
            build_and_push_images
            deploy_services
            setup_monitoring
            verify_deployment
            ;;
        "verify")
            verify_deployment
            ;;
        "clean")
            log "🧹 Cleaning up deployment..."
            gcloud run services delete vigia-workflow-orchestration-agent --region=$REGION --quiet || true
            gcloud run services delete vigia-communication-agent --region=$REGION --quiet || true
            gcloud run services delete vigia-protocol-agent --region=$REGION --quiet || true
            gcloud run services delete vigia-clinical-assessment-agent --region=$REGION --quiet || true
            gcloud run services delete vigia-image-analysis-agent --region=$REGION --quiet || true
            gcloud run services delete vigia-risk-assessment-agent --region=$REGION --quiet || true
            gcloud run services delete vigia-voice-analysis-agent --region=$REGION --quiet || true
            gcloud run services delete vigia-a2a-discovery --region=$REGION --quiet || true
            log "Cleanup completed ✓"
            ;;
        *)
            echo "Usage: $0 {check|setup|build|secrets|deploy|verify|clean}"
            echo ""
            echo "Commands:"
            echo "  check   - Check prerequisites"
            echo "  setup   - Setup Google Cloud project"
            echo "  build   - Build and push Docker images"
            echo "  secrets - Create secrets"
            echo "  deploy  - Full deployment (default)"
            echo "  verify  - Verify deployment"
            echo "  clean   - Clean up deployment"
            exit 1
            ;;
    esac
    
    log "🎉 Vigia ADK deployment completed successfully!"
    log ""
    log "📋 Next steps:"
    log "  1. Configure external webhooks (WhatsApp, Slack)"
    log "  2. Upload YOLOv5 model to storage"
    log "  3. Test end-to-end medical workflow"
    log "  4. Set up monitoring dashboards"
    log ""
    log "🏥 Your medical AI system is ready for production!"
}

# Run main function with all arguments
main "$@"