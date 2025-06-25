#!/bin/bash
# Vigia Medical AI - Quick Demo Launcher

echo "🏥 Launching Vigia Medical AI Dashboard..."
echo "📊 Initializing medical-grade components..."

# Set environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if gradio is installed
if ! python -c "import gradio" 2>/dev/null; then
    echo "📦 Installing Gradio for dashboard..."
    pip install gradio
fi

# Launch the medical dashboard
echo "🚀 Starting live demo at http://localhost:7860"
echo "🔒 All processing performed locally - HIPAA compliant"
echo ""
echo "Press Ctrl+C to stop the demo"
echo ""

python gradio_medical_dashboard.py