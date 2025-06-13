#!/usr/bin/env python3
"""
Train YOLOv5 on AZH Wound Dataset
===============================
"""

import os
import torch
from pathlib import Path

def train_azh_model():
    """Train YOLOv5 model on AZH wound dataset."""
    
    # Check if data.yaml exists
    if not Path("data.yaml").exists():
        print("Error: data.yaml not found. Run create_azh_yolo_dataset.py first.")
        return False
    
    # Clone YOLOv5 if needed
    yolo_dir = Path("yolov5")
    if not yolo_dir.exists():
        print("Cloning YOLOv5 repository...")
        os.system("git clone https://github.com/ultralytics/yolov5.git")
    
    # Change to YOLOv5 directory
    os.chdir("yolov5")
    
    # Install requirements
    os.system("pip install -r requirements.txt")
    
    # Training parameters optimized for medical images
    training_command = [
        "python", "train.py",
        "--data", "../data.yaml",
        "--weights", "yolov5s.pt",
        "--epochs", "200",  # More epochs for medical data
        "--batch-size", "8",  # Smaller batch for medical images
        "--img-size", "640",
        "--name", "azh_wound_detection",
        "--patience", "30",  # Early stopping
        "--save-period", "10"  # Save checkpoints
    ]
    
    print("Starting AZH wound detection training...")
    print(f"Command: {' '.join(training_command)}")
    
    result = os.system(" ".join(training_command))
    
    if result == 0:
        print("Training completed successfully!")
        print("Model saved in: runs/train/azh_wound_detection/weights/best.pt")
        return True
    else:
        print("Training failed!")
        return False

if __name__ == "__main__":
    train_azh_model()
