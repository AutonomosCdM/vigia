
# Vigia Dataset Integration Instructions

## Configuration
- Config file: datasets/vigia_integration_config.json
- Preprocessing: datasets/preprocess_medical_images.py
- Training: datasets/train_lpp_model.py

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
