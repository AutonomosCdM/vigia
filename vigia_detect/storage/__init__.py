"""
Medical Storage Module
=====================

Comprehensive medical data storage and retrieval system:
- Medical image storage with HIPAA compliance
- Patient progress tracking and timeline generation
- Secure file handling with encryption
- PHI anonymization and audit trails
"""

from .medical_image_storage import (
    MedicalImageStorage,
    ImageMetadata,
    MedicalImageRecord,
    ImageProcessingStatus,
    ImageType,
    AnatomicalRegion,
    store_patient_image,
    get_patient_progress
)

__all__ = [
    "MedicalImageStorage",
    "ImageMetadata", 
    "MedicalImageRecord",
    "ImageProcessingStatus",
    "ImageType",
    "AnatomicalRegion",
    "store_patient_image",
    "get_patient_progress"
]