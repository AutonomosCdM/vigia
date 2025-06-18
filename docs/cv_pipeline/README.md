# Vigia CV Pipeline Module

## Overview
This module implements the computer vision pipeline for processing images and detecting Lesiones por Presión (LPP) within the ADK (Agent Development Kit) architecture. It includes components for image preprocessing and YOLOv5-based detection integrated with the ImageAnalysisAgent.

## Project Structure
The `cv_pipeline` module is located in `vigia_detect/cv_pipeline/`.
- `__init__.py`: Initializes the module and exposes key classes.
- `detector.py`: Implements the `LPPDetector` class for YOLOv5 inference.
- `preprocessor.py`: Implements the `ImagePreprocessor` class for image transformations.
- `tests/`: Contains unit tests for the pipeline components.
    - `test_detector.py`: Tests for the `LPPDetector`.
    - `test_preprocessor.py`: Tests for the `ImagePreprocessor`.
    - `data/`: Sample images for testing.

## Features
- **Image Preprocessing:**
    - Resizing to a target size (default 640x640).
    - Normalization of pixel values.
    - Optional removal of EXIF metadata for privacy.
    - Optional face detection and blurring for privacy.
    - Optional contrast enhancement for better erythema identification.
- **LPP Detection:**
    - Wrapper around a YOLOv5 model trained for pressure ulcer detection.
    - Supports different YOLOv5 model types (`yolov5s`, `yolov5m`, `yolov5l`).
    - Configurable confidence threshold for detections.
    - Extracts bounding boxes, confidence scores, and stage classifications (0-4).

## Installation
The core dependencies for this module are included in the project's centralized requirements.
```bash
pip install -r config/requirements.txt
```
Note: The YOLOv5 model itself is loaded via `torch.hub`. For the specific YOLOv5-Wound model, manual download or cloning as a submodule might be required in a production setup (currently uses a generic model as a placeholder).

## Usage
The `cv_pipeline` module is typically used by the ImageAnalysisAgent within the ADK architecture or the CLI (`vigia_detect/cli/process_images_refactored.py`).

### Example Usage (within ADK Agent):
```python
from vigia_detect.cv_pipeline import ImagePreprocessor, LPPDetector
import cv2

# Initialize preprocessor and detector
preprocessor = ImagePreprocessor(target_size=(640, 640), enhance_contrast=True)
detector = LPPDetector(model_type='yolov5s', conf_threshold=0.3)

# Load and preprocess an image
image_path = 'path/to/your/image.jpg'
processed_image = preprocessor.preprocess(image_path)

# Perform detection
detection_results = detector.detect(processed_image)

# Process results
if detection_results['detections']:
    print(f"Detected {len(detection_results['detections'])} LPPs:")
    for det in detection_results['detections']:
        print(f"- Stage: {det['stage']}, Confidence: {det['confidence']:.2f}, Bbox: {det['bbox']}")
else:
    print("No LPPs detected.")

# You can also visualize results using image_utils
# from vigia_detect.utils.image_utils import save_detection_result
# output_path = 'path/to/save/annotated_image.jpg'
# save_detection_result(processed_image, detection_results, output_path)
```

## Development Notes
- **Model Integration:** The current implementation uses `torch.hub.load` with a generic YOLOv5 model. For the specific YOLOv5-Wound model (`calisma/pressure-ulcer`), the model weights need to be downloaded or the repository cloned and referenced correctly in `detector.py`.
- **Face Detection:** The face detection feature relies on OpenCV's Haar Cascades. Ensure OpenCV is installed with the necessary data files.
- **Testing:** Comprehensive unit tests are provided in the `tests/` subdirectory. Run them frequently during development.

## ADK Integration
This module integrates with the ImageAnalysisAgent (`vigia_detect/agents/image_analysis_agent.py`) for medical image processing within the agent-based architecture.

## See Also
- [ADK Agents Documentation](../architecture/)
- [Medical Decision Engine](../medical/)
- [CLI Documentation](../setup/)
