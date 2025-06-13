#!/usr/bin/env python3
"""
Vigia Integration Script for Medical Image Datasets
This script demonstrates how to integrate downloaded datasets with the Vigia CV pipeline.
"""

import sys
import os
from pathlib import Path
import logging
import json
from typing import Dict, List, Tuple, Optional

# Add Vigia modules to path
vigia_root = Path(__file__).parent.parent.parent
sys.path.append(str(vigia_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VigiaDatasetIntegrator:
    """Integrates medical datasets with Vigia CV pipeline"""
    
    def __init__(self, datasets_dir: str = "./datasets"):
        self.datasets_dir = Path(datasets_dir)
        self.vigia_root = vigia_root
        
    def validate_vigia_structure(self) -> bool:
        """Validate that Vigia structure is available"""
        
        required_paths = [
            self.vigia_root / "vigia_detect",
            self.vigia_root / "vigia_detect" / "cv_pipeline",
            self.vigia_root / "vigia_detect" / "systems",
        ]
        
        for path in required_paths:
            if not path.exists():
                logger.error(f"Required Vigia path not found: {path}")
                return False
        
        logger.info("✓ Vigia structure validated")
        return True
    
    def create_dataset_config(self) -> Dict:
        """Create configuration for dataset integration"""
        
        config = {
            "datasets": {
                "ham10000": {
                    "path": str(self.datasets_dir / "ham10000"),
                    "type": "skin_lesions",
                    "classes": ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"],
                    "use_for": "transfer_learning",
                    "preprocessing": {
                        "resize": [224, 224],
                        "normalize": True,
                        "augmentation": ["rotation", "flip", "brightness"]
                    }
                },
                "piid": {
                    "path": str(self.datasets_dir / "piid"),
                    "type": "pressure_ulcers",
                    "classes": ["stage_1", "stage_2", "stage_3", "stage_4"],
                    "use_for": "primary_training",
                    "preprocessing": {
                        "resize": [299, 299],
                        "normalize": True,
                        "augmentation": ["rotation", "flip", "brightness", "contrast"]
                    }
                },
                "isic": {
                    "path": str(self.datasets_dir / "isic"),
                    "type": "skin_lesions_extended",
                    "classes": ["melanoma", "nevus", "seborrheic_keratosis", "basal_cell_carcinoma"],
                    "use_for": "supplementary_training",
                    "preprocessing": {
                        "resize": [224, 224],
                        "normalize": True,
                        "augmentation": ["rotation", "flip"]
                    }
                }
            },
            "training_strategy": {
                "phase_1": {
                    "description": "Transfer learning on general skin lesions",
                    "dataset": "ham10000",
                    "epochs": 50,
                    "learning_rate": 0.001
                },
                "phase_2": {
                    "description": "Fine-tuning on pressure ulcers",
                    "dataset": "piid",
                    "epochs": 100,
                    "learning_rate": 0.0001
                },
                "phase_3": {
                    "description": "Final validation and testing",
                    "dataset": "piid",
                    "validation_split": 0.2,
                    "test_split": 0.1
                }
            },
            "integration": {
                "cv_pipeline_path": str(self.vigia_root / "vigia_detect" / "cv_pipeline"),
                "model_output_path": str(self.vigia_root / "models"),
                "preprocessing_script": "preprocess_medical_images.py",
                "training_script": "train_lpp_model.py"
            }
        }
        
        return config
    
    def create_preprocessing_script(self) -> str:
        """Create preprocessing script for medical images"""
        
        script_content = '''#!/usr/bin/env python3
"""
Medical Image Preprocessing for Vigia LPP Detection
Integrates with CV pipeline for pressure ulcer detection
"""

import cv2
import numpy as np
from PIL import Image
import albumentations as A
from pathlib import Path
from typing import Tuple, Optional

class MedicalImagePreprocessor:
    """Preprocesses medical images for LPP detection"""
    
    def __init__(self, target_size: Tuple[int, int] = (224, 224)):
        self.target_size = target_size
        self.augmentation_pipeline = A.Compose([
            A.Resize(height=target_size[0], width=target_size[1]),
            A.RandomRotate90(p=0.5),
            A.Flip(p=0.5),
            A.RandomBrightnessContrast(p=0.3),
            A.HueSaturationValue(p=0.3),
            A.GaussNoise(p=0.2),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
    def preprocess_image(self, image_path: str, augment: bool = False) -> np.ndarray:
        """Preprocess single medical image"""
        
        # Load image
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Apply preprocessing
        if augment:
            augmented = self.augmentation_pipeline(image=image)
            processed_image = augmented["image"]
        else:
            # Basic preprocessing without augmentation
            resized = cv2.resize(image, self.target_size)
            normalized = resized.astype(np.float32) / 255.0
            processed_image = (normalized - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
        
        return processed_image
    
    def batch_preprocess(self, image_paths: list, output_dir: str, augment: bool = False):
        """Batch preprocess multiple images"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        for i, img_path in enumerate(image_paths):
            try:
                processed = self.preprocess_image(img_path, augment=augment)
                output_file = output_path / f"processed_{i:05d}.npy"
                np.save(output_file, processed)
                
                if i % 100 == 0:
                    print(f"Processed {i}/{len(image_paths)} images")
                    
            except Exception as e:
                print(f"Error processing {img_path}: {e}")

def main():
    """Main preprocessing function"""
    
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess medical images for Vigia")
    parser.add_argument("--input_dir", required=True, help="Input directory with medical images")
    parser.add_argument("--output_dir", required=True, help="Output directory for processed images")
    parser.add_argument("--size", default="224,224", help="Target size as width,height")
    parser.add_argument("--augment", action="store_true", help="Apply data augmentation")
    
    args = parser.parse_args()
    
    # Parse target size
    width, height = map(int, args.size.split(','))
    target_size = (height, width)
    
    # Initialize preprocessor
    preprocessor = MedicalImagePreprocessor(target_size=target_size)
    
    # Get image paths
    input_path = Path(args.input_dir)
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    image_paths = []
    
    for ext in image_extensions:
        image_paths.extend(list(input_path.rglob(ext)))
    
    print(f"Found {len(image_paths)} images to process")
    
    # Process images
    preprocessor.batch_preprocess(image_paths, args.output_dir, augment=args.augment)
    
    print(f"Preprocessing complete! Processed images saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
'''
        
        return script_content
    
    def create_training_integration_script(self) -> str:
        """Create training script that integrates with Vigia"""
        
        script_content = '''#!/usr/bin/env python3
"""
Training Integration for Vigia LPP Detection
Connects medical datasets with Vigia CV pipeline
"""

import sys
from pathlib import Path
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as transforms
from sklearn.model_selection import train_test_split
import numpy as np
from PIL import Image

# Add Vigia modules
vigia_root = Path(__file__).parent.parent.parent
sys.path.append(str(vigia_root))

try:
    from vigia_detect.cv_pipeline.yolo_detector import YOLODetector
    from vigia_detect.systems.clinical_processing import ClinicalProcessor
    VIGIA_AVAILABLE = True
except ImportError:
    print("Vigia modules not available - running in standalone mode")
    VIGIA_AVAILABLE = False

class MedicalImageDataset(Dataset):
    """Dataset class for medical images"""
    
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        image = Image.open(self.image_paths[idx]).convert('RGB')
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

class VigiaTrainingIntegrator:
    """Integrates dataset training with Vigia pipeline"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def prepare_datasets(self, dataset_name: str):
        """Prepare dataset for training"""
        
        dataset_config = self.config['datasets'][dataset_name]
        dataset_path = Path(dataset_config['path'])
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        
        # Collect images and labels
        image_paths = []
        labels = []
        
        # Implementation depends on dataset structure
        # This is a template - adjust based on actual dataset organization
        
        return image_paths, labels
    
    def create_data_loaders(self, dataset_name: str, batch_size: int = 32):
        """Create PyTorch data loaders"""
        
        image_paths, labels = self.prepare_datasets(dataset_name)
        
        # Split data
        train_paths, val_paths, train_labels, val_labels = train_test_split(
            image_paths, labels, test_size=0.2, stratify=labels, random_state=42
        )
        
        # Define transforms
        train_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomRotation(30),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        val_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Create datasets
        train_dataset = MedicalImageDataset(train_paths, train_labels, train_transform)
        val_dataset = MedicalImageDataset(val_paths, val_labels, val_transform)
        
        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        return train_loader, val_loader
    
    def integrate_with_vigia(self, model_path: str):
        """Integrate trained model with Vigia pipeline"""
        
        if not VIGIA_AVAILABLE:
            print("Vigia modules not available - skipping integration")
            return
        
        # Initialize Vigia components
        try:
            clinical_processor = ClinicalProcessor()
            
            # Load trained model and integrate
            print(f"Integrating model from {model_path} with Vigia pipeline")
            
            # This would involve updating the CV pipeline configuration
            # to use the newly trained model for LPP detection
            
        except Exception as e:
            print(f"Error integrating with Vigia: {e}")

def main():
    """Main training integration function"""
    
    import argparse
    parser = argparse.ArgumentParser(description="Integrate dataset training with Vigia")
    parser.add_argument("--config", required=True, help="Dataset configuration file")
    parser.add_argument("--dataset", required=True, help="Dataset name to train on")
    parser.add_argument("--output", required=True, help="Output directory for trained models")
    
    args = parser.parse_args()
    
    # Initialize integrator
    integrator = VigiaTrainingIntegrator(args.config)
    
    # Create data loaders
    train_loader, val_loader = integrator.create_data_loaders(args.dataset)
    
    print(f"Training data: {len(train_loader.dataset)} samples")
    print(f"Validation data: {len(val_loader.dataset)} samples")
    
    # Training would happen here
    # This is a template - actual training implementation depends on model architecture
    
    print("Training integration template created successfully!")
    print("Implement actual training loop based on your model architecture.")

if __name__ == "__main__":
    main()
'''
        
        return script_content
    
    def generate_integration_files(self) -> None:
        """Generate all integration files"""
        
        logger.info("Generating Vigia integration files...")
        
        # Create configuration
        config = self.create_dataset_config()
        config_path = self.datasets_dir / "vigia_integration_config.json"
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✓ Configuration saved: {config_path}")
        
        # Create preprocessing script
        preprocessing_script = self.create_preprocessing_script()
        preprocessing_path = self.datasets_dir / "preprocess_medical_images.py"
        
        with open(preprocessing_path, 'w') as f:
            f.write(preprocessing_script)
        
        os.chmod(preprocessing_path, 0o755)
        logger.info(f"✓ Preprocessing script saved: {preprocessing_path}")
        
        # Create training integration script
        training_script = self.create_training_integration_script()
        training_path = self.datasets_dir / "train_lpp_model.py"
        
        with open(training_path, 'w') as f:
            f.write(training_script)
        
        os.chmod(training_path, 0o755)
        logger.info(f"✓ Training integration script saved: {training_path}")
        
        # Create usage instructions
        instructions = f"""
# Vigia Dataset Integration Instructions

## Configuration
- Config file: {config_path}
- Preprocessing: {preprocessing_path}
- Training: {training_path}

## Usage Examples:

### 1. Preprocess Images
```bash
./preprocess_medical_images.py --input_dir datasets/ham10000 --output_dir processed/ham10000 --size 224,224 --augment
```

### 2. Train LPP Model
```bash
./train_lpp_model.py --config vigia_integration_config.json --dataset piid --output models/lpp_detector
```

### 3. Integration with Vigia CV Pipeline
The trained models can be integrated with the Vigia CV pipeline:
- Update `vigia_detect/cv_pipeline/yolo_detector.py` to use new models
- Configure `vigia_detect/systems/clinical_processing.py` for LPP analysis
- Test with `vigia_detect/cli/process_images_refactored.py`

## Training Strategy:
1. Phase 1: Transfer learning on HAM10000 (general skin lesions)
2. Phase 2: Fine-tuning on PIID (specific pressure ulcers)
3. Phase 3: Integration with Vigia medical decision engine

See vigia_integration_config.json for detailed configuration.
"""
        
        instructions_path = self.datasets_dir / "VIGIA_INTEGRATION.md"
        with open(instructions_path, 'w') as f:
            f.write(instructions)
        
        logger.info(f"✓ Instructions saved: {instructions_path}")
        
        print("\n" + "="*80)
        print("VIGIA INTEGRATION FILES GENERATED")
        print("="*80)
        print(f"📋 Configuration: {config_path}")
        print(f"🔧 Preprocessing: {preprocessing_path}")
        print(f"🏋️  Training: {training_path}")
        print(f"📖 Instructions: {instructions_path}")
        print("\nNext steps:")
        print("1. Download datasets using download_datasets.py")
        print("2. Preprocess images for training")
        print("3. Train LPP detection model")
        print("4. Integrate with Vigia CV pipeline")

def main():
    """Main function"""
    
    integrator = VigiaDatasetIntegrator()
    
    # Validate Vigia structure
    if not integrator.validate_vigia_structure():
        logger.error("Vigia structure validation failed")
        sys.exit(1)
    
    # Generate integration files
    integrator.generate_integration_files()

if __name__ == "__main__":
    main()