#!/usr/bin/env python3
"""
Train YOLOv5 Model on Pressure Ulcer Dataset
===========================================

This script trains a YOLOv5 model on the pressure ulcer dataset.
"""

import os
import sys
import torch
from pathlib import Path

def train_model():
    """Train YOLOv5 model on pressure ulcer dataset."""
    
    # Check if data.yaml exists
    if not Path("data.yaml").exists():
        print("Error: data.yaml not found. Please download the dataset first.")
        return False
    
    # Install YOLOv5 if not available
    yolo_dir = Path("yolov5")
    if not yolo_dir.exists():
        print("Cloning YOLOv5 repository...")
        os.system("git clone https://github.com/ultralytics/yolov5.git")
    
    # Change to YOLOv5 directory
    os.chdir("yolov5")
    
    # Install requirements
    os.system("pip install -r requirements.txt")
    
    # Run training
    training_command = [
        "python", "train.py",
        "--data", "../data.yaml",
        "--weights", "yolov5s.pt",
        "--epochs", "100",
        "--batch-size", "16",
        "--img-size", "640",
        "--name", "pressure_ulcer_detection"
    ]
    
    print("Starting training...")
    print(f"Command: {' '.join(training_command)}")
    
    result = os.system(" ".join(training_command))
    
    if result == 0:
        print("Training completed successfully!")
        print("Model saved in: runs/train/pressure_ulcer_detection/weights/best.pt")
        return True
    else:
        print("Training failed!")
        return False

if __name__ == "__main__":
    train_model()
