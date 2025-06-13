#!/usr/bin/env python3
"""
Quick LPP Detection Model Training
==================================

Fast training script for pressure ulcer detection using available datasets.
Uses pre-trained weights and transfer learning for quick results.
"""

import os
import sys
import time
import shutil
from pathlib import Path
import subprocess

class QuickLPPTrainer:
    """Quick trainer for LPP detection model."""
    
    def __init__(self, dataset_path="./azh_yolo_dataset"):
        self.dataset_path = Path(dataset_path)
        self.yolo_path = self.dataset_path / "yolov5"
        self.model_output_dir = Path("../models/lpp_detection")
        
    def train_quick_model(self):
        """Train model with quick settings for immediate results."""
        print("=" * 60)
        print("QUICK LPP DETECTION MODEL TRAINING")
        print("=" * 60)
        
        # Verify dataset exists
        if not self.dataset_path.exists():
            print(f"Error: Dataset not found at {self.dataset_path}")
            return False
        
        # Setup YOLOv5
        if not self._setup_yolo():
            return False
        
        # Run quick training
        if not self._run_quick_training():
            return False
        
        # Copy model to vigia
        if not self._deploy_model():
            return False
        
        print("✅ Quick training completed successfully!")
        return True
    
    def _setup_yolo(self):
        """Setup YOLOv5 environment."""
        print("Setting up YOLOv5...")
        
        # Clone if needed
        if not self.yolo_path.exists():
            cmd = f"cd {self.dataset_path} && git clone https://github.com/ultralytics/yolov5.git"
            if os.system(cmd) != 0:
                print("Failed to clone YOLOv5")
                return False
        
        # Install minimal requirements
        print("Installing requirements...")
        cmd = f"cd {self.yolo_path} && pip install torch torchvision ultralytics"
        if os.system(cmd) != 0:
            print("Warning: Some requirements may not be installed")
        
        return True
    
    def _run_quick_training(self):
        """Run quick training with minimal epochs."""
        print("Starting quick training (5 epochs for demo)...")
        
        # Quick training command
        training_args = [
            "python", "train.py",
            "--data", "../data.yaml",
            "--weights", "yolov5s.pt",
            "--epochs", "5",  # Very quick for demo
            "--batch-size", "4",
            "--img-size", "320",  # Smaller for speed
            "--name", "quick_lpp_demo",
            "--patience", "10",
            "--device", "cpu"  # Use CPU for compatibility
        ]
        
        # Change to YOLOv5 directory and run training
        cmd = f"cd {self.yolo_path} && {' '.join(training_args)}"
        print(f"Running: {cmd}")
        
        start_time = time.time()
        result = os.system(cmd)
        training_time = time.time() - start_time
        
        print(f"Training completed in {training_time:.1f} seconds")
        
        if result == 0:
            print("✅ Training successful!")
            return True
        else:
            print("❌ Training failed!")
            return False
    
    def _deploy_model(self):
        """Copy trained model to Vigia models directory."""
        print("Deploying model to Vigia...")
        
        # Find the trained model
        model_path = self.yolo_path / "runs/train/quick_lpp_demo/weights/best.pt"
        
        if not model_path.exists():
            print(f"Error: Trained model not found at {model_path}")
            return False
        
        # Create models directory
        self.model_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy model
        dest_path = self.model_output_dir / "pressure_ulcer_yolov5_quick.pt"
        shutil.copy2(model_path, dest_path)
        
        print(f"✅ Model deployed to: {dest_path}")
        
        # Update model path in Vigia config
        self._update_vigia_config(dest_path)
        
        return True
    
    def _update_vigia_config(self, model_path):
        """Update Vigia configuration to use the new model."""
        config_path = Path("../../config/settings.py")
        
        if config_path.exists():
            print(f"✅ Update config manually to use: {model_path}")
        else:
            print("⚠️ Vigia config not found - update manually")

def main():
    """Main training function."""
    trainer = QuickLPPTrainer()
    
    print("Starting quick LPP detection training...")
    print("This will create a basic model for immediate testing.")
    
    success = trainer.train_quick_model()
    
    if success:
        print("\n" + "=" * 60)
        print("QUICK TRAINING COMPLETED!")
        print("=" * 60)
        print("✅ Basic LPP detection model ready")
        print("✅ Model deployed to models/lpp_detection/")
        print("\nNext steps:")
        print("1. Test model with real images")
        print("2. Run full training with more epochs")
        print("3. Integrate with Vigia pipeline")
        return 0
    else:
        print("❌ Quick training failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())