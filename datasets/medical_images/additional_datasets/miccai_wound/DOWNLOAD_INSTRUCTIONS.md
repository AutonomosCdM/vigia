# MICCAI Wound Segmentation Dataset Download Instructions

## Dataset Information
- **Name**: MICCAI Wound Segmentation Dataset
- **Description**: Medical challenge dataset with precise segmentation masks
- **Type**: wound_segmentation
- **Images**: 500+
- **Relevance Score**: 9.0/10

## Manual Download Steps

1. **Registration Required**
   - Visit: https://miccai2022.org/
   - Create account or sign in
   - Accept terms and conditions

2. **Dataset Access**
   - Navigate to datasets section
   - Search for wound segmentation datasets
   - Download training and validation sets

3. **File Organization**
   ```
   additional_datasets/miccai_wound/
   ├── images/           # Raw medical images
   ├── masks/            # Segmentation masks
   ├── annotations/      # Additional annotations
   └── metadata/         # Dataset metadata
   ```

4. **Post-Download**
   ```bash
   python ../analyze_datasets.py miccai_wound
   ```

## Papers and References
- Main paper: Various MICCAI papers
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
