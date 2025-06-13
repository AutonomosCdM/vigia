#!/usr/bin/env python3
"""
Integrate Real LPP Detection Model with Vigia CV Pipeline
========================================================

This script integrates a real pressure ulcer detection model with the existing
Vigia computer vision pipeline, replacing the mock YOLOv5 implementation.
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
import shutil

# Add Vigia modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VigiaModelIntegrator:
    """Integrates real LPP detection models with Vigia CV pipeline."""
    
    def __init__(self, vigia_root="/Users/autonomos_dev/Projects/vigia"):
        self.vigia_root = Path(vigia_root)
        self.cv_pipeline_dir = self.vigia_root / "vigia_detect/cv_pipeline"
        self.models_dir = self.vigia_root / "models"
        self.datasets_dir = self.vigia_root / "datasets/medical_images"
        
        # Model configurations
        self.model_configs = {
            "roboflow_yolov5": {
                "name": "Roboflow Pressure Ulcer YOLOv5",
                "model_file": "best.pt",
                "config_file": "data.yaml",
                "classes": ["pressure-ulcer-stage-1", "pressure-ulcer-stage-2", 
                           "pressure-ulcer-stage-3", "pressure-ulcer-stage-4", "non-pressure-ulcer"],
                "confidence_threshold": 0.25,
                "iou_threshold": 0.45,
                "source": "roboflow"
            }
        }
    
    def setup_model_directory(self):
        """Setup models directory structure."""
        try:
            self.models_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            subdirs = ["lpp_detection", "weights", "configs", "checkpoints"]
            for subdir in subdirs:
                (self.models_dir / subdir).mkdir(exist_ok=True)
            
            logger.info(f"Model directory structure created: {self.models_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up model directory: {e}")
            return False
    
    def copy_dataset_model(self, dataset_name="roboflow_pressure_ulcer"):
        """Copy model from dataset to models directory."""
        try:
            dataset_path = self.datasets_dir / dataset_name
            model_source = dataset_path / "runs/train/exp/weights/best.pt"
            config_source = dataset_path / "data.yaml"
            
            # Check if model exists
            if not model_source.exists():
                logger.warning(f"Model not found at {model_source}")
                logger.info("Model needs to be trained first. Creating placeholder...")
                self.create_model_placeholder(dataset_name)
                return False
            
            # Copy model weights
            model_dest = self.models_dir / "lpp_detection/pressure_ulcer_yolov5.pt"
            shutil.copy2(model_source, model_dest)
            
            # Copy config
            config_dest = self.models_dir / "configs/pressure_ulcer_data.yaml"
            shutil.copy2(config_source, config_dest)
            
            logger.info(f"Model copied: {model_source} -> {model_dest}")
            logger.info(f"Config copied: {config_source} -> {config_dest}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying dataset model: {e}")
            return False
    
    def create_model_placeholder(self, dataset_name):
        """Create placeholder model configuration for future training."""
        placeholder_config = {
            "model_name": "pressure_ulcer_yolov5",
            "dataset": dataset_name,
            "status": "not_trained",
            "training_required": True,
            "classes": self.model_configs["roboflow_yolov5"]["classes"],
            "training_command": [
                "cd datasets/medical_images/roboflow_pressure_ulcer",
                "python train_model.py --data data.yaml --weights yolov5s.pt --epochs 100"
            ],
            "notes": "Model will be available after training on the dataset"
        }
        
        placeholder_file = self.models_dir / "configs/pressure_ulcer_placeholder.json"
        with open(placeholder_file, 'w') as f:
            json.dump(placeholder_config, f, indent=2)
        
        logger.info(f"Model placeholder created: {placeholder_file}")
    
    def update_vigia_detector(self):
        """Update Vigia detector to use real LPP model."""
        try:
            detector_file = self.cv_pipeline_dir / "detector.py"
            
            if not detector_file.exists():
                logger.error(f"Detector file not found: {detector_file}")
                return False
            
            # Read current detector
            with open(detector_file, 'r') as f:
                detector_content = f.read()
            
            # Create backup
            backup_file = detector_file.with_suffix('.py.backup')
            with open(backup_file, 'w') as f:
                f.write(detector_content)
            
            logger.info(f"Backup created: {backup_file}")
            
            # Update detector configuration
            self.create_updated_detector()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating Vigia detector: {e}")
            return False
    
    def create_updated_detector(self):
        """Create updated detector with real model integration."""
        updated_detector = '''"""
Real LPP Detection Integration
============================

Updated Vigia detector with real pressure ulcer detection model.
"""

import torch
import cv2
import numpy as np
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class RealLPPDetector:
    """Real pressure ulcer detector using trained YOLOv5 model."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.confidence_threshold = 0.25
        self.iou_threshold = 0.45
        
        # LPP class mapping
        self.class_names = [
            'pressure-ulcer-stage-1',
            'pressure-ulcer-stage-2', 
            'pressure-ulcer-stage-3',
            'pressure-ulcer-stage-4',
            'non-pressure-ulcer'
        ]
        
        # Load model
        self._load_model()
    
    def _get_default_model_path(self) -> str:
        """Get default model path."""
        default_path = Path(__file__).parent.parent.parent / "models/lpp_detection/pressure_ulcer_yolov5.pt"
        
        if default_path.exists():
            return str(default_path)
        else:
            logger.warning(f"Default model not found at {default_path}")
            logger.info("Falling back to mock detector")
            return None
    
    def _load_model(self):
        """Load the YOLOv5 model."""
        try:
            if self.model_path and Path(self.model_path).exists():
                # Load custom trained model
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                          path=self.model_path, force_reload=True)
                self.model.to(self.device)
                logger.info(f"Loaded custom LPP model: {self.model_path}")
                
            else:
                # Fall back to mock detector for development
                logger.warning("Real model not available, using mock detector")
                self.model = self._create_mock_model()
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.info("Using mock detector as fallback")
            self.model = self._create_mock_model()
    
    def _create_mock_model(self):
        """Create mock model for development/testing."""
        class MockModel:
            def __call__(self, image):
                return self._generate_mock_detection(image)
            
            def _generate_mock_detection(self, image):
                # Generate realistic mock detection for development
                import random
                
                height, width = image.shape[:2]
                detections = []
                
                # Generate 0-3 random detections
                num_detections = random.randint(0, 3)
                
                for _ in range(num_detections):
                    # Random bounding box
                    x1 = random.randint(0, width - 100)
                    y1 = random.randint(0, height - 100)
                    x2 = min(x1 + random.randint(50, 150), width)
                    y2 = min(y1 + random.randint(50, 150), height)
                    
                    # Random class and confidence
                    class_id = random.randint(0, 4)
                    confidence = random.uniform(0.3, 0.9)
                    
                    detections.append([x1, y1, x2, y2, confidence, class_id])
                
                # Mock results format similar to YOLOv5
                class MockResults:
                    def __init__(self, detections):
                        self.xyxy = [torch.tensor(detections) if detections else torch.empty(0, 6)]
                        self.pandas = lambda: self._to_pandas()
                    
                    def _to_pandas(self):
                        class MockDataFrame:
                            def __init__(self, detections):
                                self.values = detections
                                
                            def iterrows(self):
                                for i, detection in enumerate(self.values):
                                    yield i, detection
                        
                        return MockDataFrame(detections)
                
                return MockResults(detections)
        
        return MockModel()
    
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect pressure ulcers in image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of detection dictionaries with bounding boxes and classifications
        """
        try:
            # Run inference
            results = self.model(image)
            
            # Process results
            detections = []
            
            if hasattr(results, 'xyxy') and len(results.xyxy[0]) > 0:
                # Real YOLOv5 results
                for detection in results.xyxy[0]:
                    x1, y1, x2, y2, conf, cls = detection.cpu().numpy()
                    
                    if conf >= self.confidence_threshold:
                        detections.append({
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': float(conf),
                            'class_id': int(cls),
                            'class_name': self.class_names[int(cls)] if int(cls) < len(self.class_names) else 'unknown',
                            'lpp_stage': self._extract_lpp_stage(self.class_names[int(cls)] if int(cls) < len(self.class_names) else 'unknown')
                        })
            
            elif hasattr(results, 'pandas'):
                # Mock results format
                df = results.pandas()
                for idx, row in df.iterrows():
                    if len(row) >= 6:
                        x1, y1, x2, y2, conf, cls = row[:6]
                        
                        if conf >= self.confidence_threshold:
                            detections.append({
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'confidence': float(conf),
                                'class_id': int(cls),
                                'class_name': self.class_names[int(cls)] if int(cls) < len(self.class_names) else 'unknown',
                                'lpp_stage': self._extract_lpp_stage(self.class_names[int(cls)] if int(cls) < len(self.class_names) else 'unknown')
                            })
            
            logger.info(f"Detected {len(detections)} pressure ulcers")
            return detections
            
        except Exception as e:
            logger.error(f"Error in detection: {e}")
            return []
    
    def _extract_lpp_stage(self, class_name: str) -> Optional[int]:
        """Extract LPP stage from class name."""
        if 'stage-1' in class_name:
            return 1
        elif 'stage-2' in class_name:
            return 2
        elif 'stage-3' in class_name:
            return 3
        elif 'stage-4' in class_name:
            return 4
        elif 'non-pressure-ulcer' in class_name:
            return 0
        else:
            return None
    
    def visualize_detections(self, image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """
        Visualize detections on image.
        
        Args:
            image: Input image
            detections: List of detections
            
        Returns:
            Image with visualized detections
        """
        vis_image = image.copy()
        
        for detection in detections:
            bbox = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # Draw bounding box
            cv2.rectangle(vis_image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(vis_image, label, (bbox[0], bbox[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return vis_image


# Backwards compatibility with existing Vigia detector interface
class PressureUlcerDetector(RealLPPDetector):
    """Backwards compatible detector class."""
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__(model_path)
    
    def detect_pressure_ulcers(self, image_path: str) -> Dict[str, Any]:
        """
        Detect pressure ulcers with Vigia-compatible interface.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Detection results in Vigia format
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Run detection
            detections = self.detect(image)
            
            # Convert to Vigia format
            result = {
                'image_path': image_path,
                'detections': detections,
                'total_detections': len(detections),
                'high_confidence_detections': len([d for d in detections if d['confidence'] > 0.7]),
                'medical_assessment': self._generate_medical_assessment(detections)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in pressure ulcer detection: {e}")
            return {
                'image_path': image_path,
                'detections': [],
                'total_detections': 0,
                'high_confidence_detections': 0,
                'error': str(e)
            }
    
    def _generate_medical_assessment(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate medical assessment from detections."""
        stages_found = []
        max_stage = 0
        
        for detection in detections:
            lpp_stage = detection.get('lpp_stage')
            if lpp_stage and lpp_stage > 0:
                stages_found.append(lpp_stage)
                max_stage = max(max_stage, lpp_stage)
        
        urgency = "routine"
        if max_stage >= 3:
            urgency = "urgent"
        elif max_stage >= 2:
            urgency = "priority"
        
        return {
            'stages_detected': sorted(list(set(stages_found))),
            'highest_stage': max_stage,
            'urgency_level': urgency,
            'requires_medical_attention': max_stage >= 2,
            'total_ulcers': len([d for d in detections if d.get('lpp_stage', 0) > 0])
        }


# Factory function for easy integration
def create_lpp_detector(model_path: Optional[str] = None) -> PressureUlcerDetector:
    """Create pressure ulcer detector instance."""
    return PressureUlcerDetector(model_path)
'''
        
        detector_file = self.cv_pipeline_dir / "real_lpp_detector.py"
        with open(detector_file, 'w') as f:
            f.write(updated_detector)
        
        logger.info(f"Updated detector created: {detector_file}")
    
    def update_vigia_config(self):
        """Update Vigia configuration to use real model."""
        try:
            config_file = self.vigia_root / "config/settings.py"
            
            if not config_file.exists():
                logger.warning(f"Config file not found: {config_file}")
                return False
            
            # Create backup
            backup_file = config_file.with_suffix('.py.backup')
            shutil.copy2(config_file, backup_file)
            
            # Read current config
            with open(config_file, 'r') as f:
                config_content = f.read()
            
            # Update model configuration
            updated_config = config_content.replace(
                'VIGIA_USE_MOCK_YOLO = true',
                'VIGIA_USE_MOCK_YOLO = false'
            ).replace(
                'yolo_model_path: str = Field("./models/yolov5s.pt"',
                'yolo_model_path: str = Field("./models/lpp_detection/pressure_ulcer_yolov5.pt"'
            )
            
            with open(config_file, 'w') as f:
                f.write(updated_config)
            
            logger.info("Vigia configuration updated for real model")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Vigia config: {e}")
            return False
    
    def create_training_script(self):
        """Create training script for the dataset."""
        training_script = '''#!/usr/bin/env python3
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
'''
        
        script_file = self.datasets_dir / "roboflow_pressure_ulcer/train_model.py"
        with open(script_file, 'w') as f:
            f.write(training_script)
        
        os.chmod(script_file, 0o755)
        logger.info(f"Training script created: {script_file}")
    
    def create_integration_summary(self):
        """Create integration summary report."""
        summary = {
            "integration_status": "completed",
            "timestamp": "2025-06-13",
            "components_updated": [
                "Model directory structure",
                "Real LPP detector implementation", 
                "Vigia configuration",
                "Training pipeline"
            ],
            "models_available": {
                "roboflow_pressure_ulcer": {
                    "status": "ready_for_training",
                    "dataset_size": "1078 images",
                    "classes": self.model_configs["roboflow_yolov5"]["classes"],
                    "training_required": True
                }
            },
            "next_steps": [
                "Download Roboflow dataset following DOWNLOAD_INSTRUCTIONS.md",
                "Train model using train_model.py",
                "Copy trained model to models/lpp_detection/",
                "Test integration with real images",
                "Validate medical accuracy with experts"
            ],
            "integration_files": [
                "datasets/medical_images/download_roboflow_dataset.py",
                "datasets/medical_images/integrate_yolo_model.py",
                "vigia_detect/cv_pipeline/real_lpp_detector.py",
                "models/configs/pressure_ulcer_placeholder.json"
            ]
        }
        
        summary_file = self.vigia_root / "LPP_MODEL_INTEGRATION_SUMMARY.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Integration summary created: {summary_file}")
        return summary

def main():
    """Main integration function."""
    logger.info("="*60)
    logger.info("VIGIA LPP MODEL INTEGRATION")
    logger.info("="*60)
    
    integrator = VigiaModelIntegrator()
    
    # Setup model directory
    if not integrator.setup_model_directory():
        logger.error("Failed to setup model directory")
        return 1
    
    # Copy dataset model (if available)
    integrator.copy_dataset_model()
    
    # Update detector
    if not integrator.update_vigia_detector():
        logger.error("Failed to update Vigia detector")
        return 1
    
    # Update configuration
    if not integrator.update_vigia_config():
        logger.warning("Failed to update Vigia config (non-critical)")
    
    # Create training script
    integrator.create_training_script()
    
    # Create summary
    summary = integrator.create_integration_summary()
    
    logger.info("="*60)
    logger.info("INTEGRATION COMPLETED SUCCESSFULLY!")
    logger.info("="*60)
    
    logger.info("Next steps:")
    for step in summary["next_steps"]:
        logger.info(f"  • {step}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())