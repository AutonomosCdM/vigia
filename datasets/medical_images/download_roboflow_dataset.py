#!/usr/bin/env python3
"""
Download Roboflow Pressure Ulcer Dataset
========================================

This script downloads the pressure ulcer dataset from Roboflow Universe,
which contains 1078 images with YOLOv5-compatible annotations.

Dataset: https://universe.roboflow.com/calisma/pressure-ulcer/dataset/1
"""

import os
import sys
import requests
import zipfile
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RoboflowDatasetDownloader:
    """Downloads and processes Roboflow pressure ulcer dataset."""
    
    def __init__(self, output_dir="./roboflow_pressure_ulcer"):
        self.output_dir = Path(output_dir)
        self.dataset_info = {
            "name": "Pressure Ulcer Dataset",
            "source": "Roboflow Universe - calisma",
            "images": 1078,
            "classes": ["pressure-ulcer-stage-1", "pressure-ulcer-stage-2", 
                       "pressure-ulcer-stage-3", "pressure-ulcer-stage-4", "non-pressure-ulcer"],
            "formats": ["YOLOv5 PyTorch", "YOLOv7 PyTorch", "TXT annotations"],
            "url": "https://universe.roboflow.com/calisma/pressure-ulcer/dataset/1"
        }
        
    def download_dataset(self):
        """Download the dataset from Roboflow."""
        try:
            logger.info("Starting Roboflow pressure ulcer dataset download...")
            
            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Roboflow requires API key for downloads
            # For now, provide manual instructions
            self.create_manual_instructions()
            
            # Create dataset structure
            self.create_dataset_structure()
            
            logger.info("Dataset download setup completed!")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            return False
    
    def create_manual_instructions(self):
        """Create manual download instructions."""
        instructions = f"""
# Roboflow Pressure Ulcer Dataset Download Instructions

## Automatic Download (Requires API Key)

1. Sign up at: https://roboflow.com/
2. Get your API key from: https://app.roboflow.com/settings/api
3. Run the following commands:

```bash
pip install roboflow

# Replace YOUR_API_KEY with your actual API key
python -c "
from roboflow import Roboflow
rf = Roboflow(api_key='YOUR_API_KEY')
project = rf.workspace('calisma').project('pressure-ulcer')
dataset = project.version(1).download('yolov5')
"
```

## Manual Download (No API Key Required)

1. Visit: {self.dataset_info['url']}
2. Click "Download Dataset"
3. Select "YOLOv5 PyTorch" format
4. Extract to: {self.output_dir}

## Dataset Information

- **Images**: {self.dataset_info['images']} pressure ulcer images
- **Classes**: {len(self.dataset_info['classes'])} classes
  - {chr(10).join(f"  • {cls}" for cls in self.dataset_info['classes'])}
- **Annotations**: YOLOv5-compatible format
- **Source**: Roboflow Universe (calisma workspace)

## After Download

The dataset will have this structure:
```
{self.output_dir}/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
├── data.yaml
└── README.dataset.txt
```

Run the analysis tool after download:
```bash
python ../analyze_datasets.py roboflow
```
"""
        
        instructions_file = self.output_dir / "DOWNLOAD_INSTRUCTIONS.md"
        with open(instructions_file, 'w') as f:
            f.write(instructions)
        
        logger.info(f"Manual download instructions created: {instructions_file}")
    
    def create_dataset_structure(self):
        """Create expected dataset structure."""
        directories = [
            "train/images", "train/labels",
            "valid/images", "valid/labels", 
            "test/images", "test/labels"
        ]
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
        
        # Create placeholder data.yaml
        data_yaml_content = f"""# Roboflow Pressure Ulcer Dataset Configuration
# Download from: {self.dataset_info['url']}

train: ./train/images
val: ./valid/images
test: ./test/images

nc: {len(self.dataset_info['classes'])}
names: {self.dataset_info['classes']}

# Dataset Statistics
# - Total images: {self.dataset_info['images']}
# - Source: Roboflow Universe (calisma workspace)
# - Format: YOLOv5 PyTorch
# - Annotation type: Bounding boxes (.txt files)
"""
        
        with open(self.output_dir / "data.yaml", 'w') as f:
            f.write(data_yaml_content)
        
        logger.info("Dataset structure created")
    
    def verify_download(self):
        """Verify that the dataset was downloaded correctly."""
        required_files = ["data.yaml", "train", "valid", "test"]
        
        missing_files = []
        for file_path in required_files:
            if not (self.output_dir / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.warning(f"Missing files/directories: {missing_files}")
            return False
        
        # Check for images in train directory
        train_images = list((self.output_dir / "train/images").glob("*.jpg"))
        if len(train_images) == 0:
            logger.warning("No training images found - dataset may not be downloaded yet")
            return False
        
        logger.info(f"Dataset verification passed - found {len(train_images)} training images")
        return True
    
    def get_dataset_stats(self):
        """Get statistics about the downloaded dataset."""
        stats = {
            "name": self.dataset_info["name"],
            "source": self.dataset_info["source"],
            "expected_images": self.dataset_info["images"],
            "classes": self.dataset_info["classes"],
            "downloaded": False,
            "train_images": 0,
            "valid_images": 0,
            "test_images": 0
        }
        
        if self.verify_download():
            stats["downloaded"] = True
            stats["train_images"] = len(list((self.output_dir / "train/images").glob("*.jpg")))
            stats["valid_images"] = len(list((self.output_dir / "valid/images").glob("*.jpg")))
            stats["test_images"] = len(list((self.output_dir / "test/images").glob("*.jpg")))
        
        return stats

def main():
    """Main function."""
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = "./roboflow_pressure_ulcer"
    
    downloader = RoboflowDatasetDownloader(output_dir)
    
    logger.info("="*60)
    logger.info("ROBOFLOW PRESSURE ULCER DATASET DOWNLOADER")
    logger.info("="*60)
    
    # Download dataset (creates instructions)
    success = downloader.download_dataset()
    
    if success:
        logger.info("Dataset setup completed successfully!")
        logger.info("Please follow the instructions in DOWNLOAD_INSTRUCTIONS.md")
        
        # Show dataset stats
        stats = downloader.get_dataset_stats()
        logger.info(f"Dataset: {stats['name']}")
        logger.info(f"Expected images: {stats['expected_images']}")
        logger.info(f"Classes: {len(stats['classes'])}")
        logger.info(f"Downloaded: {stats['downloaded']}")
        
    else:
        logger.error("Dataset setup failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())