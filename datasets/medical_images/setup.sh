#!/bin/bash
# Setup script for Medical Image Datasets
# Vigia Project - LPP Detection System

echo "=========================================="
echo "Setting up Medical Image Dataset Tools"
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Error installing dependencies"
    exit 1
fi

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x download_datasets.py
chmod +x analyze_datasets.py

if [ $? -eq 0 ]; then
    echo "✓ Scripts are now executable"
else
    echo "❌ Error making scripts executable"
    exit 1
fi

# Create datasets directory
echo ""
echo "Creating datasets directory structure..."
mkdir -p datasets/{ham10000,isic,piid,analysis_plots}

if [ $? -eq 0 ]; then
    echo "✓ Directory structure created"
else
    echo "❌ Error creating directories"
    exit 1
fi

# Check Kaggle API configuration
echo ""
echo "Checking Kaggle API configuration..."
if [ -f ~/.kaggle/kaggle.json ]; then
    echo "✓ Kaggle API configured"
    echo "  Ready to download HAM10000 dataset"
else
    echo "⚠️  Kaggle API not configured"
    echo "  To download HAM10000:"
    echo "  1. Go to https://www.kaggle.com/account"
    echo "  2. Create API token"
    echo "  3. Place kaggle.json in ~/.kaggle/"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure Kaggle API (if not done)"
echo "2. Run: ./download_datasets.py all"
echo "3. Run: ./analyze_datasets.py all"
echo ""
echo "For manual datasets:"
echo "- PIID: https://github.com/FU-MedicalAI/PIID"
echo "- ISIC: https://www.isic-archive.com/"
echo ""
echo "See README.md for detailed instructions."