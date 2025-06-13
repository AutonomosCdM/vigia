#!/usr/bin/env python3
"""
Dataset Download Script for Medical Image Analysis
Vigia Project - Pressure Ulcer Detection System

This script downloads and verifies medical image datasets for LPP detection.
"""

import os
import sys
import requests
import kaggle
import zipfile
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatasetDownloader:
    """Handles downloading and verification of medical image datasets"""
    
    def __init__(self, base_dir: str = "./datasets"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
    def download_ham10000(self) -> bool:
        """
        Download HAM10000 dataset from Kaggle
        
        Returns:
            bool: Success status
        """
        logger.info("Downloading HAM10000 dataset from Kaggle...")
        
        ham_dir = self.base_dir / "ham10000"
        ham_dir.mkdir(exist_ok=True)
        
        try:
            # Check if Kaggle API is configured
            try:
                from kaggle.api.kaggle_api_extended import KaggleApi
                api = KaggleApi()
                api.authenticate()
            except Exception as e:
                logger.error(f"Kaggle API not configured: {e}")
                logger.info("Please configure Kaggle API:")
                logger.info("1. Go to https://www.kaggle.com/account")
                logger.info("2. Create API token")
                logger.info("3. Place kaggle.json in ~/.kaggle/")
                return False
            
            # Download dataset
            api.dataset_download_files(
                'kmader/skin-cancer-mnist-ham10000',
                path=str(ham_dir),
                unzip=True
            )
            
            logger.info(f"HAM10000 dataset downloaded to: {ham_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading HAM10000: {e}")
            return False
    
    def download_isic_sample(self) -> bool:
        """
        Download ISIC dataset sample (requires manual registration)
        
        Returns:
            bool: Success status
        """
        logger.info("ISIC dataset requires manual download...")
        logger.info("Steps to download ISIC:")
        logger.info("1. Register at https://www.isic-archive.com/")
        logger.info("2. Browse to https://challenge.isic-archive.com/data/")
        logger.info("3. Download training data")
        logger.info("4. Extract to ./datasets/isic/")
        
        isic_dir = self.base_dir / "isic"
        isic_dir.mkdir(exist_ok=True)
        
        # Check if already downloaded
        if any(isic_dir.iterdir()):
            logger.info(f"ISIC data found in: {isic_dir}")
            return True
        
        return False
    
    def request_piid_access(self) -> bool:
        """
        Provide instructions for accessing PIID dataset
        
        Returns:
            bool: Always returns False as manual action required
        """
        logger.info("PIID dataset requires manual access request...")
        logger.info("Steps to access PIID:")
        logger.info("1. Visit: https://github.com/FU-MedicalAI/PIID")
        logger.info("2. Open issue requesting dataset access")
        logger.info("3. Access Google Drive: https://drive.google.com/drive/u/0/folders/12JouktrzXIo6ywpSe2OYWRYNNIxlEKvK")
        logger.info("4. Download and extract to ./datasets/piid/")
        
        piid_dir = self.base_dir / "piid"
        piid_dir.mkdir(exist_ok=True)
        
        # Check if already downloaded
        if any(piid_dir.iterdir()):
            logger.info(f"PIID data found in: {piid_dir}")
            return True
        
        return False
    
    def verify_dataset_structure(self, dataset_name: str) -> Dict[str, any]:
        """
        Verify dataset structure and provide summary
        
        Args:
            dataset_name: Name of dataset to verify
            
        Returns:
            Dict with dataset information
        """
        dataset_dir = self.base_dir / dataset_name
        
        if not dataset_dir.exists():
            return {"exists": False, "error": "Dataset directory not found"}
        
        # Count files by extension
        file_counts = {}
        total_size = 0
        
        for file_path in dataset_dir.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                file_counts[ext] = file_counts.get(ext, 0) + 1
                total_size += file_path.stat().st_size
        
        # Convert size to human readable
        size_mb = total_size / (1024 * 1024)
        
        return {
            "exists": True,
            "path": str(dataset_dir),
            "file_counts": file_counts,
            "total_files": sum(file_counts.values()),
            "size_mb": round(size_mb, 2),
            "image_files": file_counts.get('.jpg', 0) + file_counts.get('.png', 0) + file_counts.get('.jpeg', 0)
        }
    
    def create_dataset_summary(self) -> None:
        """Create summary of all available datasets"""
        
        logger.info("Creating dataset summary...")
        
        datasets = ['ham10000', 'isic', 'piid']
        summary = {}
        
        for dataset in datasets:
            summary[dataset] = self.verify_dataset_structure(dataset)
        
        # Print summary
        print("\n" + "="*80)
        print("DATASET SUMMARY")
        print("="*80)
        
        for dataset, info in summary.items():
            print(f"\n{dataset.upper()}:")
            if info["exists"]:
                print(f"  ✅ Path: {info['path']}")
                print(f"  📁 Total files: {info['total_files']}")
                print(f"  🖼️  Image files: {info['image_files']}")
                print(f"  💾 Size: {info['size_mb']} MB")
                print(f"  📋 File types: {dict(info['file_counts'])}")
            else:
                print(f"  ❌ Not available: {info.get('error', 'Unknown error')}")
        
        print("\n" + "="*80)
    
    def download_all(self) -> None:
        """Download all available datasets"""
        
        logger.info("Starting dataset download process...")
        
        # Download HAM10000 (automatic if Kaggle configured)
        logger.info("\n1. Downloading HAM10000...")
        self.download_ham10000()
        
        # ISIC instructions
        logger.info("\n2. ISIC Dataset...")
        self.download_isic_sample()
        
        # PIID instructions  
        logger.info("\n3. PIID Dataset...")
        self.request_piid_access()
        
        # Create summary
        logger.info("\n4. Creating summary...")
        self.create_dataset_summary()

def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = "all"
    
    downloader = DatasetDownloader()
    
    if command == "ham10000":
        downloader.download_ham10000()
    elif command == "isic":
        downloader.download_isic_sample()
    elif command == "piid":
        downloader.request_piid_access()
    elif command == "summary":
        downloader.create_dataset_summary()
    elif command == "all":
        downloader.download_all()
    else:
        print("Usage: python download_datasets.py [ham10000|isic|piid|summary|all]")
        sys.exit(1)

if __name__ == "__main__":
    main()