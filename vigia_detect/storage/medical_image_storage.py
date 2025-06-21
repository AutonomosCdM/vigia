"""
Medical Image Storage Service
============================

Comprehensive image storage system for patient medical records with:
- Secure image upload and storage
- Patient progress tracking
- Clinical image metadata management
- HIPAA-compliant file handling
- Integration with tokenized patient system
"""

import os
import uuid
import asyncio
import hashlib
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
import logging
from PIL import Image, ExifTags
import aiofiles

from ..core.phi_tokenization_client import TokenizedPatient
from ..db.supabase_client_refactored import SupabaseClientRefactored as SupabaseClient
from ..utils.secure_logger import SecureLogger
from ..utils.audit_service import AuditService, AuditEventType, AuditSeverity

logger = SecureLogger("medical_image_storage")


class ImageProcessingStatus(Enum):
    """Image processing status states"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageType(Enum):
    """Medical image type classifications"""
    PRESSURE_INJURY_ASSESSMENT = "pressure_injury_assessment"
    WOUND_PROGRESS = "wound_progress"
    BASELINE_SKIN = "baseline_skin"
    POST_TREATMENT = "post_treatment"
    CLINICAL_DOCUMENTATION = "clinical_documentation"


class AnatomicalRegion(Enum):
    """Anatomical regions for medical images"""
    SACRUM = "sacrum"
    HEEL = "heel"
    ELBOW = "elbow"
    SHOULDER_BLADE = "shoulder_blade"
    HIP = "hip"
    ANKLE = "ankle"
    KNEE = "knee"
    OTHER = "other"


@dataclass
class ImageMetadata:
    """Medical image metadata structure"""
    filename: str
    file_size: int
    image_format: str
    dimensions: str
    anatomical_region: AnatomicalRegion
    image_type: ImageType
    clinical_context: str
    processing_status: ImageProcessingStatus = ImageProcessingStatus.PENDING
    storage_url: Optional[str] = None
    encryption_key_id: Optional[str] = None


@dataclass
class MedicalImageRecord:
    """Complete medical image record"""
    image_id: str
    token_id: str
    metadata: ImageMetadata
    uploaded_at: datetime
    uploaded_by: str
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None


class MedicalImageStorage:
    """
    Medical Image Storage Service
    
    Handles secure storage, retrieval, and tracking of medical images
    for tokenized patients with complete audit trail and progress tracking.
    """
    
    def __init__(self, storage_base_path: Optional[str] = None):
        self.db_client = SupabaseClient()
        self.audit_service = AuditService()
        
        # Configure storage paths
        self.storage_base_path = Path(storage_base_path or os.getenv(
            "MEDICAL_IMAGE_STORAGE_PATH", 
            "/Users/autonomos_dev/Projects/vigia/vigia_detect/data/medical_images"
        ))
        
        # Create storage directories
        self._initialize_storage_structure()
        
        logger.audit("medical_image_storage_initialized", {
            "storage_path": str(self.storage_base_path),
            "encryption_enabled": True,
            "audit_enabled": True
        })
    
    def _initialize_storage_structure(self):
        """Initialize secure storage directory structure"""
        directories = [
            self.storage_base_path,
            self.storage_base_path / "originals",
            self.storage_base_path / "processed", 
            self.storage_base_path / "thumbnails",
            self.storage_base_path / "progress_sequences",
            self.storage_base_path / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Set secure permissions (owner read/write only)
        for directory in directories:
            os.chmod(directory, 0o700)
    
    async def store_medical_image(
        self,
        image_file_path: Union[str, Path],
        tokenized_patient: TokenizedPatient,
        anatomical_region: AnatomicalRegion,
        image_type: ImageType,
        clinical_context: str,
        uploaded_by: str = "vigia_system"
    ) -> MedicalImageRecord:
        """
        Store medical image with comprehensive metadata and security
        
        Args:
            image_file_path: Path to the image file
            tokenized_patient: Tokenized patient data (NO PHI)
            anatomical_region: Anatomical location of the image
            image_type: Type of medical image
            clinical_context: Clinical description (NO PHI)
            uploaded_by: System identifier for uploader
            
        Returns:
            MedicalImageRecord with complete storage information
        """
        try:
            image_path = Path(image_file_path)
            
            # Generate unique image ID
            image_id = str(uuid.uuid4())
            
            # Extract and validate image metadata
            metadata = await self._extract_image_metadata(
                image_path, anatomical_region, image_type, clinical_context
            )
            
            # Anonymize image (remove EXIF data)
            anonymized_path = await self._anonymize_image(image_path, image_id)
            
            # Store in secure location
            storage_url = await self._store_image_securely(
                anonymized_path, tokenized_patient.token_id, image_id
            )
            
            # Update metadata with storage info
            metadata.storage_url = storage_url
            metadata.encryption_key_id = self._generate_encryption_key_id(image_id)
            
            # Create database record
            image_record = MedicalImageRecord(
                image_id=image_id,
                token_id=tokenized_patient.token_id,
                metadata=metadata,
                uploaded_at=datetime.now(timezone.utc),
                uploaded_by=uploaded_by
            )
            
            # Insert into database
            await self._create_database_record(image_record)
            
            # Generate thumbnail for quick viewing
            await self._generate_thumbnail(anonymized_path, image_id)
            
            # Audit log
            await self.audit_service.log_event(
                event_type=AuditEventType.DATA_CREATED,
                component="medical_image_storage",
                action="medical_image_stored",
                session_id=f"img_storage_{image_id}",
                details={
                    "image_id": image_id,
                    "token_id": tokenized_patient.token_id,
                    "patient_alias": tokenized_patient.patient_alias,
                    "anatomical_region": anatomical_region.value,
                    "image_type": image_type.value,
                    "file_size": metadata.file_size,
                    "storage_url": storage_url
                }
            )
            
            logger.info(f"Medical image stored successfully", {
                "image_id": image_id,
                "patient_alias": tokenized_patient.patient_alias,
                "anatomical_region": anatomical_region.value
            })
            
            return image_record
            
        except Exception as e:
            logger.error(f"Failed to store medical image: {e}")
            await self.audit_service.log_event(
                event_type=AuditEventType.ERROR_OCCURRED,
                component="medical_image_storage",
                action="medical_image_storage_failed",
                session_id=f"img_storage_error_{uuid.uuid4()}",
                details={
                    "error": str(e),
                    "token_id": tokenized_patient.token_id,
                    "patient_alias": tokenized_patient.patient_alias
                }
            )
            raise
    
    async def get_patient_images(
        self, 
        token_id: str,
        anatomical_region: Optional[AnatomicalRegion] = None,
        image_type: Optional[ImageType] = None,
        limit: int = 50
    ) -> List[MedicalImageRecord]:
        """
        Retrieve all images for a tokenized patient
        
        Args:
            token_id: Tokenized patient identifier
            anatomical_region: Filter by anatomical region
            image_type: Filter by image type
            limit: Maximum number of images to return
            
        Returns:
            List of medical image records
        """
        try:
            # Build query filters
            filters = {"token_id": token_id}
            if anatomical_region:
                filters["anatomical_region"] = anatomical_region.value
            if image_type:
                filters["image_type"] = image_type.value
            
            # Query database
            result = await self.db_client.query(
                table="medical_images",
                filters=filters,
                order_by="uploaded_at",
                limit=limit
            )
            
            # Convert to MedicalImageRecord objects
            image_records = []
            for row in result:
                metadata = ImageMetadata(
                    filename=row["filename"],
                    file_size=row["file_size"],
                    image_format=row["image_format"],
                    dimensions=row["dimensions"],
                    anatomical_region=AnatomicalRegion(row["anatomical_region"]),
                    image_type=ImageType(row["image_type"]),
                    clinical_context=row["clinical_context"],
                    processing_status=ImageProcessingStatus(row["processing_status"]),
                    storage_url=row["storage_url"],
                    encryption_key_id=row["encryption_key_id"]
                )
                
                image_record = MedicalImageRecord(
                    image_id=row["image_id"],
                    token_id=row["token_id"],
                    metadata=metadata,
                    uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
                    uploaded_by=row["uploaded_by"],
                    processing_started_at=datetime.fromisoformat(row["processing_started_at"]) if row["processing_started_at"] else None,
                    processing_completed_at=datetime.fromisoformat(row["processing_completed_at"]) if row["processing_completed_at"] else None
                )
                
                image_records.append(image_record)
            
            logger.audit("patient_images_retrieved", {
                "token_id": token_id,
                "image_count": len(image_records),
                "anatomical_region": anatomical_region.value if anatomical_region else "all",
                "image_type": image_type.value if image_type else "all"
            })
            
            return image_records
            
        except Exception as e:
            logger.error(f"Failed to retrieve patient images: {e}")
            raise
    
    async def get_progress_timeline(
        self,
        token_id: str,
        anatomical_region: AnatomicalRegion
    ) -> List[Dict[str, Any]]:
        """
        Get chronological progress timeline for specific anatomical region
        
        Args:
            token_id: Tokenized patient identifier
            anatomical_region: Anatomical region to track
            
        Returns:
            Chronological list of progress entries with images and analysis
        """
        try:
            # Get all images for this region, chronologically ordered
            images = await self.get_patient_images(
                token_id=token_id,
                anatomical_region=anatomical_region
            )
            
            # Get detection results for each image
            progress_timeline = []
            
            for image_record in images:
                # Get LPP detection results for this image
                detection_result = await self.db_client.query_single(
                    table="lpp_detections",
                    filters={"image_id": image_record.image_id}
                )
                
                progress_entry = {
                    "date": image_record.uploaded_at.isoformat(),
                    "image_id": image_record.image_id,
                    "image_type": image_record.metadata.image_type.value,
                    "clinical_context": image_record.metadata.clinical_context,
                    "anatomical_region": anatomical_region.value,
                    "image_url": image_record.metadata.storage_url,
                    "thumbnail_url": await self._get_thumbnail_url(image_record.image_id),
                    "lpp_detection": None
                }
                
                if detection_result:
                    progress_entry["lpp_detection"] = {
                        "lpp_detected": detection_result["lpp_detected"],
                        "lpp_grade": detection_result["lpp_grade"],
                        "confidence_score": float(detection_result["confidence_score"]) if detection_result["confidence_score"] else None,
                        "clinical_severity": detection_result["clinical_severity"],
                        "urgency_level": detection_result["urgency_level"],
                        "tissue_type": detection_result["tissue_type"],
                        "wound_dimensions": detection_result["wound_dimensions"]
                    }
                
                progress_timeline.append(progress_entry)
            
            logger.audit("progress_timeline_generated", {
                "token_id": token_id,
                "anatomical_region": anatomical_region.value,
                "timeline_entries": len(progress_timeline)
            })
            
            return progress_timeline
            
        except Exception as e:
            logger.error(f"Failed to generate progress timeline: {e}")
            raise
    
    async def update_processing_status(
        self,
        image_id: str,
        status: ImageProcessingStatus,
        processing_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update image processing status
        
        Args:
            image_id: Image identifier
            status: New processing status
            processing_details: Additional processing information
            
        Returns:
            True if update successful
        """
        try:
            update_data = {
                "processing_status": status.value
            }
            
            if status == ImageProcessingStatus.PROCESSING:
                update_data["processing_started_at"] = datetime.now(timezone.utc).isoformat()
            elif status in [ImageProcessingStatus.COMPLETED, ImageProcessingStatus.FAILED]:
                update_data["processing_completed_at"] = datetime.now(timezone.utc).isoformat()
            
            result = await self.db_client.update(
                table="medical_images",
                filters={"image_id": image_id},
                data=update_data
            )
            
            logger.audit("image_processing_status_updated", {
                "image_id": image_id,
                "new_status": status.value,
                "processing_details": processing_details or {}
            })
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to update processing status: {e}")
            return False
    
    async def _extract_image_metadata(
        self,
        image_path: Path,
        anatomical_region: AnatomicalRegion,
        image_type: ImageType,
        clinical_context: str
    ) -> ImageMetadata:
        """Extract and validate image metadata"""
        
        # Get file information
        file_size = image_path.stat().st_size
        
        # Open and analyze image
        with Image.open(image_path) as img:
            image_format = img.format
            dimensions = f"{img.width}x{img.height}"
        
        # Generate anonymized filename
        filename = f"medical_{uuid.uuid4().hex[:8]}.{image_format.lower()}"
        
        return ImageMetadata(
            filename=filename,
            file_size=file_size,
            image_format=image_format,
            dimensions=dimensions,
            anatomical_region=anatomical_region,
            image_type=image_type,
            clinical_context=clinical_context
        )
    
    async def _anonymize_image(self, image_path: Path, image_id: str) -> Path:
        """Remove EXIF data and anonymize image"""
        
        anonymized_path = self.storage_base_path / "temp" / f"anon_{image_id}.jpg"
        
        # Open image and remove EXIF data
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Save without EXIF data
            img.save(anonymized_path, "JPEG", quality=95, optimize=True)
        
        return anonymized_path
    
    async def _store_image_securely(
        self,
        image_path: Path,
        token_id: str,
        image_id: str
    ) -> str:
        """Store image in secure location with encryption"""
        
        # Create patient-specific directory
        patient_dir = self.storage_base_path / "originals" / token_id[:8]
        patient_dir.mkdir(exist_ok=True)
        os.chmod(patient_dir, 0o700)
        
        # Final storage path
        storage_path = patient_dir / f"{image_id}.jpg"
        
        # Copy to secure location
        async with aiofiles.open(image_path, 'rb') as src:
            async with aiofiles.open(storage_path, 'wb') as dst:
                await dst.write(await src.read())
        
        # Set secure permissions
        os.chmod(storage_path, 0o600)
        
        # Return relative URL for database storage
        return f"medical_images/originals/{token_id[:8]}/{image_id}.jpg"
    
    async def _generate_thumbnail(self, image_path: Path, image_id: str) -> str:
        """Generate thumbnail for quick viewing"""
        
        thumbnail_path = self.storage_base_path / "thumbnails" / f"{image_id}_thumb.jpg"
        
        with Image.open(image_path) as img:
            # Create thumbnail (max 200x200)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            img.save(thumbnail_path, "JPEG", quality=80)
        
        os.chmod(thumbnail_path, 0o600)
        
        return f"medical_images/thumbnails/{image_id}_thumb.jpg"
    
    async def _get_thumbnail_url(self, image_id: str) -> str:
        """Get thumbnail URL for image"""
        return f"medical_images/thumbnails/{image_id}_thumb.jpg"
    
    def _generate_encryption_key_id(self, image_id: str) -> str:
        """Generate encryption key identifier"""
        return f"med_img_key_{hashlib.sha256(image_id.encode()).hexdigest()[:16]}"
    
    async def _create_database_record(self, image_record: MedicalImageRecord):
        """Create database record for medical image"""
        
        data = {
            "image_id": image_record.image_id,
            "token_id": image_record.token_id,
            "filename": image_record.metadata.filename,
            "file_size": image_record.metadata.file_size,
            "image_format": image_record.metadata.image_format,
            "dimensions": image_record.metadata.dimensions,
            "anatomical_region": image_record.metadata.anatomical_region.value,
            "image_type": image_record.metadata.image_type.value,
            "clinical_context": image_record.metadata.clinical_context,
            "storage_url": image_record.metadata.storage_url,
            "encryption_key_id": image_record.metadata.encryption_key_id,
            "processing_status": image_record.metadata.processing_status.value,
            "uploaded_at": image_record.uploaded_at.isoformat(),
            "uploaded_by": image_record.uploaded_by
        }
        
        await self.db_client.insert(table="medical_images", data=data)


# Convenience functions for common operations

async def store_patient_image(
    image_file_path: str,
    tokenized_patient: TokenizedPatient,
    anatomical_region: str,
    image_type: str,
    clinical_context: str
) -> MedicalImageRecord:
    """
    Convenience function to store patient image
    
    Example:
        # Store Batman's pressure injury image
        record = await store_patient_image(
            "/path/to/image.jpg",
            batman_patient,
            "sacrum",
            "pressure_injury_assessment", 
            "Initial assessment of sacral pressure injury"
        )
    """
    storage = MedicalImageStorage()
    
    return await storage.store_medical_image(
        image_file_path=image_file_path,
        tokenized_patient=tokenized_patient,
        anatomical_region=AnatomicalRegion(anatomical_region),
        image_type=ImageType(image_type),
        clinical_context=clinical_context
    )


async def get_patient_progress(
    token_id: str,
    anatomical_region: str
) -> List[Dict[str, Any]]:
    """
    Convenience function to get patient progress timeline
    
    Example:
        # Get Batman's sacral pressure injury progress
        timeline = await get_patient_progress(
            "batman_token_id",
            "sacrum"
        )
    """
    storage = MedicalImageStorage()
    
    return await storage.get_progress_timeline(
        token_id=token_id,
        anatomical_region=AnatomicalRegion(anatomical_region)
    )


# Example usage
async def example_batman_image_storage():
    """Example of storing and tracking Batman's medical images"""
    
    # Mock tokenized patient (Batman)
    from ..core.phi_tokenization_client import TokenizedPatient
    from datetime import datetime
    
    batman = TokenizedPatient(
        token_id="batman_token_123",
        patient_alias="Batman",
        age_range="40-49",
        gender_category="male",
        risk_factors={"diabetes": False, "limited_mobility": True},
        medical_conditions={"chronic_pain": True},
        expires_at=datetime.now(timezone.utc)
    )
    
    storage = MedicalImageStorage()
    
    # Store initial pressure injury image
    record1 = await storage.store_medical_image(
        image_file_path="/path/to/initial_injury.jpg",
        tokenized_patient=batman,
        anatomical_region=AnatomicalRegion.SACRUM,
        image_type=ImageType.PRESSURE_INJURY_ASSESSMENT,
        clinical_context="Initial assessment - Stage 2 pressure injury on sacrum, 3x2 cm"
    )
    
    print(f"Stored image: {record1.image_id}")
    
    # Store follow-up image after 1 week
    record2 = await storage.store_medical_image(
        image_file_path="/path/to/followup_injury.jpg",
        tokenized_patient=batman,
        anatomical_region=AnatomicalRegion.SACRUM,
        image_type=ImageType.WOUND_PROGRESS,
        clinical_context="1-week follow-up - Improved healing, reduced inflammation"
    )
    
    print(f"Stored follow-up: {record2.image_id}")
    
    # Get complete progress timeline
    timeline = await storage.get_progress_timeline(
        token_id=batman.token_id,
        anatomical_region=AnatomicalRegion.SACRUM
    )
    
    print(f"Progress timeline: {len(timeline)} entries")
    for entry in timeline:
        print(f"  {entry['date']}: {entry['clinical_context']}")
        if entry['lpp_detection']:
            print(f"    LPP Grade: {entry['lpp_detection']['lpp_grade']}")


if __name__ == "__main__":
    # Test the image storage system
    asyncio.run(example_batman_image_storage())