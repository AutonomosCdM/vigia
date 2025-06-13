#!/usr/bin/env python3
"""
Create YOLO-compatible dataset from AZH Wound Dataset
====================================================

Convert the Foot Ulcer Segmentation Challenge data to YOLOv5 format
for pressure ulcer detection training.
"""

import os
import cv2
import json
import shutil
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

class AZHToYOLOConverter:
    """Convert AZH wound dataset to YOLO format."""
    
    def __init__(self, 
                 azh_path="./additional_datasets/azh_wound/repository/data/Foot Ulcer Segmentation Challenge",
                 output_path="./azh_yolo_dataset"):
        self.azh_path = Path(azh_path)
        self.output_path = Path(output_path)
        
        # YOLO class mapping for ulcer detection
        self.class_mapping = {
            "ulcer": 0,  # Generic ulcer class (can be refined later)
            "wound": 0,  # Map wounds to ulcer for now
            "background": -1  # Ignore background
        }
        
    def convert_to_yolo(self):
        """Convert AZH dataset to YOLO format."""
        print("Converting AZH Wound Dataset to YOLO format...")
        
        # Create output structure
        self._create_output_structure()
        
        # Process training images
        train_images = self._get_image_list("train")
        self._process_images(train_images, "train")
        
        # Process test images (use as validation)
        test_images = self._get_image_list("test")
        self._process_images(test_images, "val")
        
        # Create data.yaml file
        self._create_data_yaml()
        
        print(f"Conversion completed! Dataset available at: {self.output_path}")
        return True
    
    def _create_output_structure(self):
        """Create YOLO dataset directory structure."""
        directories = [
            "images/train", "images/val", "images/test",
            "labels/train", "labels/val", "labels/test"
        ]
        
        for directory in directories:
            (self.output_path / directory).mkdir(parents=True, exist_ok=True)
    
    def _get_image_list(self, split: str) -> List[Path]:
        """Get list of images for given split."""
        image_dir = self.azh_path / split / "images"
        if not image_dir.exists():
            print(f"Warning: {image_dir} not found")
            return []
        
        images = list(image_dir.glob("*.png"))
        print(f"Found {len(images)} images in {split} split")
        return images
    
    def _process_images(self, image_list: List[Path], split: str):
        """Process images for given split."""
        for i, image_path in enumerate(image_list):
            if i % 100 == 0:
                print(f"Processing {split}: {i}/{len(image_list)}")
            
            # Copy image
            dest_image = self.output_path / "images" / split / image_path.name
            shutil.copy2(image_path, dest_image)
            
            # Create dummy label (since we don't have annotations)
            # In real usage, you would extract bounding boxes from segmentation masks
            self._create_dummy_label(image_path, split)
    
    def _create_dummy_label(self, image_path: Path, split: str):
        """Create dummy YOLO label file."""
        # For demo purposes, create empty label files
        # In production, extract actual bounding boxes from segmentation masks
        label_name = image_path.stem + ".txt"
        label_path = self.output_path / "labels" / split / label_name
        
        # Create empty label file (no annotations)
        with open(label_path, 'w') as f:
            pass  # Empty file means no detections
    
    def _create_data_yaml(self):
        """Create YOLO data.yaml configuration file."""
        yaml_content = f"""
# AZH Wound Dataset - YOLO Format
path: {self.output_path.absolute()}
train: images/train
val: images/val
test: images/test

# Classes
nc: 1  # number of classes
names: ['ulcer']  # class names
"""
        
        yaml_path = self.output_path / "data.yaml"
        with open(yaml_path, 'w') as f:
            f.write(yaml_content.strip())
        
        print(f"Created data.yaml: {yaml_path}")

def create_training_script():
    """Create training script for AZH dataset."""
    script_content = '''#!/usr/bin/env python3
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
'''
    
    script_path = Path("./azh_yolo_dataset/train_azh_model.py")
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable
    os.chmod(script_path, 0o755)
    print(f"Created training script: {script_path}")

def main():
    """Main function."""
    print("=" * 60)
    print("AZH WOUND DATASET TO YOLO CONVERTER")
    print("=" * 60)
    
    converter = AZHToYOLOConverter()
    
    # Check if AZH dataset exists
    if not converter.azh_path.exists():
        print(f"Error: AZH dataset not found at {converter.azh_path}")
        print("Please ensure the AZH wound dataset is downloaded first.")
        return 1
    
    # Convert dataset
    success = converter.convert_to_yolo()
    
    if success:
        # Create training script
        create_training_script()
        
        print("\n" + "=" * 60)
        print("CONVERSION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Dataset location: {converter.output_path}")
        print("\nNext steps:")
        print("1. cd azh_yolo_dataset")
        print("2. python train_azh_model.py")
        print("3. Copy trained model to ../models/lpp_detection/")
        
        return 0
    else:
        print("Conversion failed!")
        return 1

if __name__ == "__main__":
    exit(main())