# LPP-Detect CLI Module

## Overview
Command line interface for batch processing wound images through the LPP detection pipeline.

## Features
- Batch processing of wound images
- YOLOv5-based lesion detection
- Stage classification (0-4)
- Results storage in Supabase or local filesystem
- Privacy protection (face blurring, EXIF removal)

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python vigia_detect/cli/process_images.py \
  --input /path/to/images \
  --output /path/to/results \
  [--patient-code PATIENT_ID] \
  [--confidence 0.25] \
  [--save-db] \
  [--model yolov5s]
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `-i`, `--input` | Input directory path | `./data/input` |
| `-o`, `--output` | Output directory path | `./data/output` |
| `--patient-code` | Patient identifier | None |
| `--confidence` | Detection confidence threshold (0.0-1.0) | 0.25 |
| `--save-db` | Save results to Supabase | False |
| `--model` | YOLOv5 model variant (`yolov5s`, `yolov5m`, `yolov5l`) | `yolov5s` |

## Output Format
Processed images are saved with detection annotations. Results include:
- Bounding boxes
- Stage classification
- Confidence scores
- Color-coded visualizations (red=stage 4, orange=stage 3, etc.)

When saving to Supabase, results include:
- Patient identifier (if provided)
- Original and processed image paths
- Detection metadata
- Processing timestamp

## Example Output
```json
{
  "filename": "wound_001.jpg",
  "results": {
    "detections": [
      {
        "bbox": [100, 150, 200, 250],
        "confidence": 0.92,
        "stage": 3,
        "class_name": "LPP-Stage3"
      }
    ],
    "processing_time_ms": 120.5
  }
}
```

## Development Notes
- Requires Python 3.8+
- Uses PyTorch for YOLOv5 inference
- Supabase integration requires valid `.env` configuration
- Test images available in `vigia_detect/data/input`

## See Also
- [API Reference](api_reference.md)
- [Developer Guide](developer_guide.md)
