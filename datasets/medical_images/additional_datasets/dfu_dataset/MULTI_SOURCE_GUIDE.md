# Diabetic Foot Ulcer Dataset Multi-Source Download Guide

## Dataset Information
- **Name**: Diabetic Foot Ulcer Dataset
- **Description**: Diabetic foot ulcers related to pressure injuries
- **Type**: diabetic_ulcers
- **Images**: 2000+
- **Relevance Score**: 7.5/10

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
