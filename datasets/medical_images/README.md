# Medical Image Datasets for LPP Detection

This directory contains tools and scripts for managing medical image datasets for the Vigia pressure ulcer detection system.

## Overview

The Vigia project requires medical image datasets for training and testing LPP (Lesiones Por Presión) detection models. This toolkit provides automated download, analysis, and evaluation capabilities for relevant medical datasets.

## Available Datasets

### 🔴 PIID (Pressure Injury Images Dataset) - PRIMARY TARGET
- **Best for**: Direct LPP detection training
- **Size**: 1,091 images (299x299 RGB)
- **Classes**: 4 pressure ulcer stages
- **Access**: Manual request required
- **Status**: ⚠️ Requires Google Drive access

### 🟢 HAM10000 - PUBLICLY AVAILABLE
- **Best for**: Transfer learning baseline
- **Size**: 10,000 dermatoscopic images  
- **Classes**: 7 skin lesion types
- **Access**: Public via Kaggle
- **Status**: ✅ Ready to download

### 🟡 ISIC Archive - REGISTRATION REQUIRED
- **Best for**: Additional skin lesion data
- **Size**: 400,000+ images
- **Classes**: Multiple skin conditions
- **Access**: Free registration required
- **Status**: ⚠️ Manual registration needed

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Kaggle API (for HAM10000)
```bash
# 1. Go to https://www.kaggle.com/account
# 2. Create API token
# 3. Place kaggle.json in ~/.kaggle/
```

### 3. Download Datasets
```bash
# Download all available datasets
./download_datasets.py all

# Download specific dataset
./download_datasets.py ham10000
./download_datasets.py isic
./download_datasets.py piid
```

### 4. Analyze Datasets
```bash
# Analyze all datasets
./analyze_datasets.py all

# Analyze specific dataset
./analyze_datasets.py ham10000
```

## Dataset Analysis Features

The analysis toolkit provides:

- **Image Properties**: Resolution, format, file sizes
- **Dataset Structure**: Directory organization, annotation files
- **Label Analysis**: Classification schemes, metadata extraction
- **LPP Suitability**: Scoring system for pressure ulcer detection relevance
- **Visualization**: Comparative charts and statistics

## Usage Examples

### Download HAM10000 Dataset
```bash
./download_datasets.py ham10000
```

### Analyze Dataset Quality
```bash
./analyze_datasets.py ham10000
```

### Generate Summary Report
```bash
./download_datasets.py summary
```

## File Structure

```
datasets/medical_images/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── download_datasets.py         # Dataset download tool
├── analyze_datasets.py          # Dataset analysis tool
├── available_datasets_analysis.md  # Comprehensive dataset review
├── datasets/                    # Downloaded datasets directory
│   ├── ham10000/               # HAM10000 skin lesion data
│   ├── isic/                   # ISIC archive data
│   ├── piid/                   # PIID pressure ulcer data
│   └── analysis_plots/         # Generated visualizations
└── analysis_results.json       # Detailed analysis results
```

## Manual Dataset Access

### PIID Dataset (Pressure Injury Images)
1. Visit: https://github.com/FU-MedicalAI/PIID
2. Open issue requesting dataset access
3. Access Google Drive: https://drive.google.com/drive/u/0/folders/12JouktrzXIo6ywpSe2OYWRYNNIxlEKvK
4. Download and extract to `./datasets/piid/`

### ISIC Archive
1. Register at: https://www.isic-archive.com/
2. Browse: https://challenge.isic-archive.com/data/
3. Download training data
4. Extract to `./datasets/isic/`

## Development Strategy

### Recommended Approach:
1. **Start with HAM10000** for baseline transfer learning
2. **Request PIID access** for specific pressure ulcer training
3. **Use ISIC** for additional skin lesion diversity
4. **Implement data augmentation** to increase effective dataset size

### Transfer Learning Pipeline:
1. Pre-train on HAM10000 (general skin lesions)
2. Fine-tune on PIID (specific pressure ulcers)
3. Validate on held-out test sets
4. Deploy with confidence thresholds

## Analysis Output

The analysis tools generate:

- **Quantitative Metrics**: Image counts, resolutions, file sizes
- **Suitability Scores**: 0-10 rating for LPP detection relevance
- **Recommendations**: Specific guidance for each dataset
- **Visualizations**: Comparative charts and distributions
- **JSON Reports**: Detailed machine-readable results

## Integration with Vigia

These datasets integrate with the Vigia medical pipeline:

- **Training Data**: For `vigia_detect/cv_pipeline/` YOLOv5 models
- **Validation**: For medical decision engine testing
- **Transfer Learning**: For pre-trained feature extraction
- **Augmentation**: For expanding limited medical datasets

## Medical Compliance

All dataset usage follows medical data guidelines:

- **Privacy**: No personal health information in public datasets
- **Licensing**: Verify academic/commercial use permissions
- **Validation**: Medical expert review of automated classifications
- **Audit Trail**: Complete lineage tracking for regulatory compliance

## Troubleshooting

### Common Issues:

1. **Kaggle API Error**: Configure ~/.kaggle/kaggle.json with API credentials
2. **Permission Denied**: Run `chmod +x *.py` to make scripts executable
3. **Missing Dependencies**: Install with `pip install -r requirements.txt`
4. **Dataset Not Found**: Check manual download instructions above

### Getting Help:

- Check the analysis report: `analysis_results.json`
- Review logs in console output
- Verify dataset paths in `datasets/` directory
- Consult medical team for clinical validation

## Next Steps

After dataset setup:

1. **Implement preprocessing pipeline** for medical images
2. **Design data augmentation** strategies for limited medical data
3. **Create training/validation splits** with medical stratification
4. **Integrate with Vigia CV pipeline** for automated LPP detection
5. **Validate with medical experts** for clinical accuracy

---

**Note**: This toolkit prioritizes medical-grade datasets suitable for clinical applications. All automated analyses should be validated by qualified medical professionals.