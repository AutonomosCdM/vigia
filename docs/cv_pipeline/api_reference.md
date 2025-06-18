# CV Pipeline API Reference

## Module: `vigia_detect.cv_pipeline`

This module provides the core components for image preprocessing and LPP detection.

### Classes

#### `LPPDetector`
Wrapper class for the YOLOv5 model used for detecting and classifying Lesiones por Presión (LPP).

```python
class LPPDetector:
    def __init__(self, model_type: str = 'yolov5s', conf_threshold: float = 0.25, model_path: Optional[str] = None):
        """
        Initializes the LPPDetector.

        Args:
            model_type: Type of YOLOv5 model ('yolov5s', 'yolov5m', 'yolov5l').
            conf_threshold: Confidence threshold for detections (0.0-1.0).
            model_path: Path to a custom pre-trained model weights file (optional).
        """
        pass # Implementation details

    def detect(self, image: Union[np.ndarray, str, Path]) -> dict:
        """
        Detects lesions in an image.

        Args:
            image: The input image as a NumPy array (BGR format) or a path to the image file.

        Returns:
            A dictionary containing detection results:
            {
                'detections': [
                    {
                        'bbox': [x1, y1, x2, y2],  # Bounding box coordinates [float]
                        'confidence': float,        # Confidence score (0-1)
                        'stage': int,              # LPP stage (0-4)
                        'class_name': str          # Class name (e.g., 'LPP-Stage1')
                    },
                    ...
                ],
                'processing_time_ms': float        # Inference time in milliseconds
            }
        """
        pass # Implementation details

    def get_model_info(self) -> dict:
        """
        Returns information about the loaded model.

        Returns:
            A dictionary with model details:
            {
                "type": str,             # Model type
                "device": str,           # Device used (e.g., 'cuda:0', 'cpu')
                "conf_threshold": float, # Configured confidence threshold
                "classes": List[str]     # List of class names
            }
        """
        pass # Implementation details

#### `ImagePreprocessor`
Class for applying various preprocessing steps to images before detection.

```python
class ImagePreprocessor:
    def __init__(self, target_size: Tuple[int, int] = (640, 640), normalize: bool = True, face_detection: bool = True,
                 enhance_contrast: bool = True, remove_exif: bool = True):
        """
        Initializes the ImagePreprocessor.

        Args:
            target_size: Target dimensions for resizing (width, height).
            normalize: Whether to normalize pixel values to [0, 1].
            face_detection: Whether to enable face detection and blurring.
            enhance_contrast: Whether to enhance image contrast (especially for erythema).
            remove_exif: Whether to remove EXIF metadata.
        """
        pass # Implementation details

    def preprocess(self, image_path: Union[str, Path, np.ndarray]) -> np.ndarray:
        """
        Preprocesses an image.

        Args:
            image_path: Path to the image file or the image as a NumPy array (BGR format).

        Returns:
            The preprocessed image as a NumPy array (BGR format).
        """
        pass # Implementation details

    def get_preprocessor_info(self) -> dict:
        """
        Returns information about the preprocessor configuration.

        Returns:
            A dictionary with configuration details:
            {
                "target_size": Tuple[int, int],
                "normalize": bool,
                "face_detection": bool,
                "enhance_contrast": bool,
                "remove_exif": bool
            }
        """
        pass # Implementation details

## Data Structures

### Detection Result Format
The `detect` method of `LPPDetector` returns a dictionary with the following structure:

```python
{
    'detections': [
        {
            'bbox': [float, float, float, float],  # [x1, y1, x2, y2]
            'confidence': float,
            'stage': int,
            'class_name': str
        },
        ... # List of detected objects
    ],
    'processing_time_ms': float # Time taken for inference
}
```

## Dependencies
- `torch`: For loading and running the YOLOv5 model.
- `numpy`: For image manipulation.
- `cv2` (OpenCV): For image processing tasks like resizing, color space conversion, and face detection.
- `PIL` (Pillow): For image loading and EXIF data handling.

## Error Handling
- Exceptions during model loading or preprocessing are logged and re-raised.
- The `detect` method handles cases with no detections gracefully by returning an empty `detections` list.

## See Also
- [CV Pipeline README](README.md)
- [CV Pipeline Developer Guide](developer_guide.md)
