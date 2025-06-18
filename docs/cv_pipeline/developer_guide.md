# CV Pipeline Developer Guide

## Overview
This guide provides instructions for developers working on the LPP-Detect computer vision pipeline module.

## Project Structure
The `cv_pipeline` module is located in `vigia_detect/cv_pipeline/`.
- `__init__.py`: Module initialization.
- `detector.py`: Contains the `LPPDetector` class.
- `preprocessor.py`: Contains the `ImagePreprocessor` class.
- `tests/`: Unit tests for the module.

## Dependencies
This module has several external dependencies, primarily for image processing and deep learning:
- `torch`: For loading and running the YOLOv5 model.
- `numpy`: For numerical operations, especially with image data.
- `cv2` (OpenCV): Used for image manipulations like resizing, color space conversions, and face detection (Haar Cascades).
- `PIL` (Pillow): Used for loading images and handling EXIF metadata.

Ensure these dependencies are installed as specified in `requirements.txt`.

## Adding New Features or Modifying Existing Ones

### Modifying `ImagePreprocessor`
1.  **Identify the preprocessing step:** Determine which part of the pipeline needs modification (e.g., adding a new transformation, adjusting parameters).
2.  **Locate relevant method:** Find the method in `preprocessor.py` responsible for that step (`_remove_exif_data`, `_detect_and_blur_faces`, `_enhance_image_contrast`, or the main `preprocess` method).
3.  **Implement changes:** Modify the code, ensuring it handles various image formats (NumPy arrays, file paths) and integrates correctly with other steps.
4.  **Update `__init__`:** If the new feature requires configuration options, add parameters to the `__init__` method and store them as instance variables.
5.  **Update tests:** Add new test cases or modify existing ones in `vigia_detect/cv_pipeline/tests/test_preprocessor.py` to verify the changes. Ensure edge cases are covered.
6.  **Update documentation:**
    *   Modify `vigia_detect_docs/cv_pipeline/README.md` to describe the new feature or changes.
    *   Update `vigia_detect_docs/cv_pipeline/api_reference.md` with any changes to method signatures, parameters, or behavior.
    *   Consider if changes are needed in the main `info.md` or sprint documentation.

### Modifying `LPPDetector`
1.  **Identify the change:** Determine the required modification (e.g., updating the model loading logic, changing post-processing of results, integrating a new model version).
2.  **Locate relevant method:** Find the method in `detector.py` responsible for the change (`_load_model`, `detect`, or `get_model_info`).
3.  **Implement changes:** Modify the code. Pay close attention to model loading paths, device handling (CPU/GPU), confidence thresholds, and how detection results are parsed and structured.
4.  **Update `__init__`:** If the change requires new configuration (e.g., a new model path parameter), add it to the `__init__` method.
5.  **Update tests:** Add new test cases or modify existing ones in `vigia_detect/cv_pipeline/tests/test_detector.py` to verify the changes. Use sample images in `tests/data/` or add new ones as needed.
6.  **Update documentation:**
    *   Modify `vigia_detect_docs/cv_pipeline/README.md` to describe the changes, especially regarding model requirements or usage.
    *   Update `vigia_detect_docs/cv_pipeline/api_reference.md` with any changes to method signatures, parameters, or the structure of detection results.
    *   Consider if changes are needed in the main `info.md` or sprint documentation.

## Integrating a New YOLOv5-Wound Model
1.  **Obtain model weights:** Download the pre-trained weights for the specific YOLOv5-Wound model (e.g., from the `calisma/pressure-ulcer` repository).
2.  **Update `_load_model`:** Modify the `_load_model` method in `detector.py` to load the model from the downloaded weights file using `torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)`.
3.  **Update `__init__`:** Ensure the `model_path` parameter is used correctly to pass the path to the weights file.
4.  **Verify class names:** Confirm that the class names used in the model match the expected LPP stages (0-4) and update `self.class_names` if necessary. Adjust the stage mapping in the `detect` method if the model's class indices don't directly correspond to stages 0-4.
5.  **Update tests:** Ensure `test_detector.py` uses the new model for testing and that the expected detection results (bounding boxes, stages, confidences) are correct for the test images with the new model.
6.  **Update documentation:** Clearly document the requirement to download the specific model weights and how to specify the `model_path` in the README and API reference.

## Testing
Run tests for the CV pipeline module using `pytest`:
```bash
pytest vigia_detect/cv_pipeline/tests/
```
Or use the project's test runner:
```bash
python run_tests.py
```
Ensure all tests pass before submitting changes. Add new test images to `vigia_detect/cv_pipeline/tests/data/` as needed.

## Code Style and Best Practices
- Follow PEP 8 guidelines.
- Use clear and descriptive variable and function names.
- Include comprehensive docstrings for all classes, methods, and functions, explaining their purpose, arguments, and return values.
- Use type hints for improved code readability and maintainability.
- Handle potential errors gracefully using `try...except` blocks and appropriate logging.
- Optimize image processing steps for performance, especially for batch processing scenarios.

## See Also
- [CV Pipeline README](README.md)
- [CV Pipeline API Reference](api_reference.md)
- [CLI Developer Guide](../cli/developer_guide.md)
