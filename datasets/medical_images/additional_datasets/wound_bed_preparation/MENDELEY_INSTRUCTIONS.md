# Wound Bed Preparation Dataset Mendeley Download Instructions

## Dataset Information
- **Name**: Wound Bed Preparation Dataset
- **Description**: Chronic wound images for tissue classification
- **Source**: Mendeley Data
- **URL**: https://data.mendeley.com/datasets/9ycv73z5v2/1
- **Paper**: https://doi.org/10.1016/j.compbiomed.2020.103906

## Download Steps

### 1. Access Mendeley Data
1. Visit: https://data.mendeley.com/datasets/9ycv73z5v2/1
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
additional_datasets/wound_bed_preparation/
├── images/           # Medical images
├── labels/           # Classification labels  
├── metadata/         # Patient/clinical data
└── documentation/    # Dataset description
```

### 4. Citation Required
If using this dataset, please cite:
```
https://doi.org/10.1016/j.compbiomed.2020.103906
```

## Integration with Vigia
This dataset provides:
- Wound tissue classification labels
- Clinical photography examples
- Baseline for wound assessment algorithms

## Quality Assessment
After download:
```bash
python ../analyze_datasets.py wound_bed_preparation
```
