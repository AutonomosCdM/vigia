#!/usr/bin/env python3
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
