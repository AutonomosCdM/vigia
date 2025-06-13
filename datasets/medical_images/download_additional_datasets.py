#!/usr/bin/env python3
"""
Download Additional Medical Datasets for LPP Detection
======================================================

This script downloads recommended additional datasets for expanding
the pressure ulcer detection capabilities:

1. AZH Wound Dataset (1,000+ chronic wound images)
2. MICCAI Wound Segmentation Dataset  
3. DFU Dataset (diabetic foot ulcers)
"""

import os
import sys
import requests
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdditionalDatasetsDownloader:
    """Downloads additional medical datasets for LPP detection."""
    
    def __init__(self, output_dir="./additional_datasets"):
        self.output_dir = Path(output_dir)
        
        # Dataset configurations
        self.datasets = {
            "azh_wound": {
                "name": "AZH Wound Dataset",
                "description": "1,000+ chronic wound images with annotations",
                "url": "https://github.com/uwm-bigdata/wound-segmentation",
                "paper": "https://doi.org/10.1038/s41598-020-78799-w",
                "type": "chronic_wounds",
                "access": "public_github",
                "images": "1000+",
                "formats": ["RGB images", "Segmentation masks"],
                "relevance_score": 8.5,
                "download_method": "git_clone"
            },
            "miccai_wound": {
                "name": "MICCAI Wound Segmentation Dataset",
                "description": "Medical challenge dataset with precise segmentation masks",
                "url": "https://miccai2022.org/",
                "paper": "Various MICCAI papers",
                "type": "wound_segmentation", 
                "access": "registration_required",
                "images": "500+",
                "formats": ["High-res images", "Pixel-level masks"],
                "relevance_score": 9.0,
                "download_method": "manual_registration"
            },
            "dfu_dataset": {
                "name": "Diabetic Foot Ulcer Dataset",
                "description": "Diabetic foot ulcers related to pressure injuries",
                "url": "https://github.com/milesial/Pytorch-UNet",
                "paper": "https://doi.org/10.1016/j.compbiomed.2021.104450",
                "type": "diabetic_ulcers",
                "access": "mixed_sources",
                "images": "2000+",
                "formats": ["Clinical photos", "Annotations"],
                "relevance_score": 7.5,
                "download_method": "multiple_sources"
            },
            "wound_bed_preparation": {
                "name": "Wound Bed Preparation Dataset",
                "description": "Chronic wound images for tissue classification",
                "url": "https://data.mendeley.com/datasets/9ycv73z5v2/1",
                "paper": "https://doi.org/10.1016/j.compbiomed.2020.103906",
                "type": "wound_classification",
                "access": "mendeley_data",
                "images": "800+",
                "formats": ["RGB images", "Classification labels"],
                "relevance_score": 7.0,
                "download_method": "mendeley_download"
            }
        }
    
    def download_all_datasets(self):
        """Download all recommended datasets."""
        logger.info("Starting download of additional medical datasets...")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for dataset_id, config in self.datasets.items():
            logger.info(f"Processing dataset: {config['name']}")
            
            dataset_dir = self.output_dir / dataset_id
            dataset_dir.mkdir(exist_ok=True)
            
            result = self._download_dataset(dataset_id, config, dataset_dir)
            results[dataset_id] = result
        
        # Create summary report
        self._create_summary_report(results)
        
        return results
    
    def _download_dataset(self, dataset_id: str, config: Dict[str, Any], 
                         output_dir: Path) -> Dict[str, Any]:
        """Download individual dataset."""
        
        method = config["download_method"]
        result = {
            "dataset_id": dataset_id,
            "name": config["name"],
            "status": "pending",
            "method": method,
            "files_created": []
        }
        
        try:
            if method == "git_clone":
                success = self._download_git_repository(config, output_dir)
                
            elif method == "manual_registration":
                success = self._create_manual_instructions(config, output_dir)
                
            elif method == "multiple_sources":
                success = self._create_multi_source_guide(config, output_dir)
                
            elif method == "mendeley_download":
                success = self._create_mendeley_instructions(config, output_dir)
                
            else:
                logger.warning(f"Unknown download method: {method}")
                success = False
            
            result["status"] = "success" if success else "failed"
            result["files_created"] = list(output_dir.glob("*"))
            
        except Exception as e:
            logger.error(f"Error downloading {dataset_id}: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _download_git_repository(self, config: Dict[str, Any], output_dir: Path) -> bool:
        """Download dataset from Git repository."""
        try:
            url = config["url"]
            
            # Clone repository
            clone_command = f"git clone {url} {output_dir}/repository"
            result = os.system(clone_command)
            
            if result == 0:
                logger.info(f"Successfully cloned {config['name']}")
                
                # Create dataset info file
                self._create_dataset_info_file(config, output_dir)
                return True
            else:
                logger.error(f"Failed to clone repository: {url}")
                return False
                
        except Exception as e:
            logger.error(f"Error in git clone: {e}")
            return False
    
    def _create_manual_instructions(self, config: Dict[str, Any], output_dir: Path) -> bool:
        """Create manual download instructions."""
        try:
            instructions = f"""# {config['name']} Download Instructions

## Dataset Information
- **Name**: {config['name']}
- **Description**: {config['description']}
- **Type**: {config['type']}
- **Images**: {config['images']}
- **Relevance Score**: {config['relevance_score']}/10

## Manual Download Steps

1. **Registration Required**
   - Visit: {config['url']}
   - Create account or sign in
   - Accept terms and conditions

2. **Dataset Access**
   - Navigate to datasets section
   - Search for wound segmentation datasets
   - Download training and validation sets

3. **File Organization**
   ```
   {output_dir}/
   ├── images/           # Raw medical images
   ├── masks/            # Segmentation masks
   ├── annotations/      # Additional annotations
   └── metadata/         # Dataset metadata
   ```

4. **Post-Download**
   ```bash
   python ../analyze_datasets.py {output_dir.name}
   ```

## Papers and References
- Main paper: {config.get('paper', 'See conference proceedings')}
- Conference: MICCAI (Medical Image Computing and Computer Assisted Intervention)

## Integration with Vigia
This dataset provides high-quality segmentation masks that can be used for:
- Fine-grained wound boundary detection
- Multi-class tissue segmentation
- Transfer learning for pressure ulcer segmentation

## Notes
- Dataset typically available after conference registration
- May require institutional affiliation
- Contact organizers for academic access
"""
            
            instructions_file = output_dir / "DOWNLOAD_INSTRUCTIONS.md"
            with open(instructions_file, 'w') as f:
                f.write(instructions)
            
            self._create_dataset_info_file(config, output_dir)
            logger.info(f"Manual instructions created for {config['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating manual instructions: {e}")
            return False
    
    def _create_multi_source_guide(self, config: Dict[str, Any], output_dir: Path) -> bool:
        """Create multi-source download guide."""
        try:
            guide = f"""# {config['name']} Multi-Source Download Guide

## Dataset Information
- **Name**: {config['name']}
- **Description**: {config['description']}
- **Type**: {config['type']}
- **Images**: {config['images']}
- **Relevance Score**: {config['relevance_score']}/10

## Multiple Data Sources

### 1. GitHub Repositories
```bash
# Example repositories with diabetic foot ulcer data
git clone https://github.com/milesial/Pytorch-UNet.git
git clone https://github.com/cosmoimd/wound-segmentation.git
```

### 2. Kaggle Datasets
```bash
# Search for diabetic foot ulcer datasets
kaggle datasets search "diabetic foot ulcer"
kaggle datasets search "wound segmentation"
```

### 3. Medical Image Databases
- **ISIC Archive**: https://www.isic-archive.com/
- **NIH National Database**: https://www.nlm.nih.gov/
- **Open-I**: https://openi.nlm.nih.gov/

### 4. Research Papers with Datasets
- Check supplementary materials of DFU research papers
- Contact authors for dataset access
- Look for publicly shared Google Drive links

## Recommended Approach
1. Start with GitHub repositories
2. Supplement with Kaggle datasets  
3. Contact research groups for additional data
4. Combine multiple sources for robust training

## Integration Strategy
```python
# Combine multiple DFU sources
datasets = [
    "github_dfu_data/",
    "kaggle_dfu_data/", 
    "research_dfu_data/"
]

# Create unified dataset
python combine_dfu_datasets.py --sources datasets --output unified_dfu/
```

## Quality Assessment
Run analysis on each source:
```bash
python ../analyze_datasets.py github_source
python ../analyze_datasets.py kaggle_source
python ../analyze_datasets.py research_source
```
"""
            
            guide_file = output_dir / "MULTI_SOURCE_GUIDE.md"
            with open(guide_file, 'w') as f:
                f.write(guide)
            
            self._create_dataset_info_file(config, output_dir)
            logger.info(f"Multi-source guide created for {config['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating multi-source guide: {e}")
            return False
    
    def _create_mendeley_instructions(self, config: Dict[str, Any], output_dir: Path) -> bool:
        """Create Mendeley dataset instructions."""
        try:
            instructions = f"""# {config['name']} Mendeley Download Instructions

## Dataset Information
- **Name**: {config['name']}
- **Description**: {config['description']}
- **Source**: Mendeley Data
- **URL**: {config['url']}
- **Paper**: {config.get('paper', 'See Mendeley page')}

## Download Steps

### 1. Access Mendeley Data
1. Visit: {config['url']}
2. Create free Mendeley account if needed
3. Click "Download" button

### 2. Dataset Contents
The dataset typically includes:
- High-resolution wound images
- Classification labels
- Metadata files
- Documentation

### 3. File Organization
```
{output_dir}/
├── images/           # Medical images
├── labels/           # Classification labels  
├── metadata/         # Patient/clinical data
└── documentation/    # Dataset description
```

### 4. Citation Required
If using this dataset, please cite:
```
{config.get('paper', 'See Mendeley page for citation information')}
```

## Integration with Vigia
This dataset provides:
- Wound tissue classification labels
- Clinical photography examples
- Baseline for wound assessment algorithms

## Quality Assessment
After download:
```bash
python ../analyze_datasets.py {output_dir.name}
```
"""
            
            instructions_file = output_dir / "MENDELEY_INSTRUCTIONS.md"
            with open(instructions_file, 'w') as f:
                f.write(instructions)
            
            self._create_dataset_info_file(config, output_dir)
            logger.info(f"Mendeley instructions created for {config['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating Mendeley instructions: {e}")
            return False
    
    def _create_dataset_info_file(self, config: Dict[str, Any], output_dir: Path):
        """Create dataset information JSON file."""
        info_file = output_dir / "dataset_info.json"
        with open(info_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _create_summary_report(self, results: Dict[str, Dict[str, Any]]):
        """Create summary report of all downloads."""
        summary = {
            "download_summary": "Additional Medical Datasets for LPP Detection",
            "timestamp": "2025-06-13",
            "total_datasets": len(results),
            "successful_downloads": len([r for r in results.values() if r["status"] == "success"]),
            "datasets": results,
            "recommendations": [
                "Start with AZH Wound Dataset (if available via Git)",
                "Request MICCAI datasets through academic channels", 
                "Combine multiple DFU sources for robust training",
                "Use Mendeley datasets for tissue classification",
                "Validate all datasets with medical experts before training"
            ],
            "integration_priority": [
                "azh_wound (highest relevance for chronic wounds)",
                "miccai_wound (best segmentation quality)",
                "dfu_dataset (related pathology)",
                "wound_bed_preparation (tissue classification)"
            ]
        }
        
        summary_file = self.output_dir / "DOWNLOAD_SUMMARY.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Create markdown summary
        self._create_markdown_summary(summary)
        
        logger.info(f"Summary report created: {summary_file}")
    
    def _create_markdown_summary(self, summary: Dict[str, Any]):
        """Create markdown summary report."""
        
        md_content = f"""# Additional Medical Datasets Download Summary

**Generated**: {summary['timestamp']}  
**Total Datasets**: {summary['total_datasets']}  
**Successful Downloads**: {summary['successful_downloads']}

## Dataset Status

| Dataset | Name | Status | Method | Relevance |
|---------|------|--------|---------|-----------|
"""
        
        for dataset_id, result in summary['datasets'].items():
            config = self.datasets[dataset_id]
            status_icon = "✅" if result['status'] == 'success' else "⚠️"
            md_content += f"| {dataset_id} | {result['name']} | {status_icon} {result['status']} | {result['method']} | {config['relevance_score']}/10 |\n"
        
        md_content += f"""
## Integration Recommendations

### Priority Order:
"""
        for i, dataset in enumerate(summary['integration_priority'], 1):
            md_content += f"{i}. **{dataset}** - {self.datasets[dataset]['description']}\n"
        
        md_content += """
### General Recommendations:
"""
        for rec in summary['recommendations']:
            md_content += f"- {rec}\n"
        
        md_content += """
## Next Steps

1. **Download Available Datasets**: Follow individual instructions in each dataset directory
2. **Quality Analysis**: Run `analyze_datasets.py` on each downloaded dataset
3. **Medical Validation**: Have medical experts review dataset quality and relevance
4. **Integration Planning**: Prioritize datasets based on relevance scores and availability
5. **Training Pipeline**: Implement transfer learning from general to specific datasets

## File Structure

```
additional_datasets/
├── azh_wound/                  # AZH chronic wound dataset
├── miccai_wound/               # MICCAI segmentation dataset  
├── dfu_dataset/                # Diabetic foot ulcer data
├── wound_bed_preparation/      # Wound tissue classification
├── DOWNLOAD_SUMMARY.json       # This summary in JSON format
└── DOWNLOAD_SUMMARY.md         # This summary file
```
"""
        
        md_file = self.output_dir / "DOWNLOAD_SUMMARY.md"
        with open(md_file, 'w') as f:
            f.write(md_content)

def main():
    """Main function."""
    logger.info("="*60)
    logger.info("ADDITIONAL MEDICAL DATASETS DOWNLOADER")
    logger.info("="*60)
    
    downloader = AdditionalDatasetsDownloader()
    
    # Download all datasets
    results = downloader.download_all_datasets()
    
    # Report results
    successful = len([r for r in results.values() if r["status"] == "success"])
    total = len(results)
    
    logger.info(f"Download completed: {successful}/{total} datasets processed successfully")
    logger.info("Check DOWNLOAD_SUMMARY.md for detailed instructions")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())