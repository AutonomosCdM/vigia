# CLI API Reference

## `process_images.py`

### `parse_args()`
```python
def parse_args() -> argparse.Namespace
```
Parses command line arguments.

**Returns:**  
Parsed arguments namespace with:
- `input`: Input directory path
- `output`: Output directory path  
- `patient_code`: Optional patient identifier
- `confidence`: Detection confidence threshold
- `save_db`: Boolean flag for Supabase storage
- `model`: YOLOv5 model variant

### `process_directory()`
```python
def process_directory(
    input_dir: str,
    output_dir: str,
    detector: LPPDetector,
    preprocessor: ImagePreprocessor,
    patient_code: Optional[str] = None,
    save_to_db: bool = False,
    db_client: Optional[SupabaseClient] = None
) -> dict
```
Processes all images in input directory.

**Parameters:**
- `input_dir`: Path to input images
- `output_dir`: Path to save results
- `detector`: Initialized LPPDetector instance
- `preprocessor`: Initialized ImagePreprocessor
- `patient_code`: Optional patient identifier
- `save_to_db`: Save results to Supabase
- `db_client`: SupabaseClient instance if saving to DB

**Returns:**  
Processing statistics dictionary:
```python
{
    "processed": int,  # Total images processed
    "detected": int,   # Images with detections
    "detections": list # Detection details
}
```

### `main()`
```python
def main() -> None
```
Entry point for CLI execution.

## Classes

### `LPPDetector`
Wrapper for YOLOv5 wound detection model.

#### Methods:
- `__init__(model_type='yolov5s', conf_threshold=0.25, model_path=None)`
- `detect(image) -> dict`: Runs detection on image
- `get_model_info() -> dict`: Returns model metadata

### `ImagePreprocessor`
Handles image preprocessing pipeline.

#### Methods:
- `__init__(target_size=(640,640), normalize=True, face_detection=True, enhance_contrast=True, remove_exif=True)`
- `preprocess(image_path) -> np.ndarray`: Processes single image
- `get_preprocessor_info() -> dict`: Returns config

## Data Structures

### Detection Result
```python
{
    "detections": [{
        "bbox": [x1, y1, x2, y2],
        "confidence": float,
        "stage": int,
        "class_name": str
    }],
    "processing_time_ms": float
}
```

### Supabase Record
```python
{
    "patient_code": str,
    "original_path": str,
    "processed_path": str,
    "detections": list,
    "processed_at": datetime
}
```

## Error Handling
- Logs errors to console with timestamps
- Continues processing on image errors
- Validates arguments before processing
