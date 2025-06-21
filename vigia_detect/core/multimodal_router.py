#!/usr/bin/env python3
"""
Multimodal Content Router
========================

Routes WhatsApp content by type to specialized processing pipelines:
- Text → NLP Medical Analysis
- Image → Computer Vision LPP Detection  
- Audio → Speech-to-Text + Medical Analysis
- Video → Frame extraction + Audio processing
- Documents → OCR + Medical Text Analysis

Handles Bruce Wayne's mixed content properly.
"""

import asyncio
import os
import sys
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json

# Add vigia_detect to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from vigia_detect.utils.secure_logger import SecureLogger
from vigia_detect.monitoring.phi_tokenizer import PHITokenizer

logger = SecureLogger(__name__)


class ContentType(Enum):
    """Types of content that can be processed"""
    TEXT = "text"
    IMAGE = "image" 
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class ProcessingPriority(Enum):
    """Medical processing priority levels"""
    EMERGENCY = "emergency"       # Immediate processing
    URGENT = "urgent"             # Within 5 minutes
    ROUTINE = "routine"           # Within 30 minutes
    SCHEDULED = "scheduled"       # Batch processing


@dataclass
class ContentItem:
    """Individual content item for processing"""
    content_type: ContentType
    content_data: Union[str, bytes, Path]
    mime_type: str
    file_path: Optional[Path] = None
    metadata: Dict[str, Any] = None
    priority: ProcessingPriority = ProcessingPriority.ROUTINE
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MultimodalMessage:
    """Complete multimodal message from WhatsApp"""
    patient_id: str
    patient_code: str
    timestamp: str
    source: str = "whatsapp"
    
    # Content items
    text_content: Optional[str] = None
    image_items: List[ContentItem] = None
    audio_items: List[ContentItem] = None
    video_items: List[ContentItem] = None
    document_items: List[ContentItem] = None
    
    # Processing metadata
    phi_tokenized: bool = False
    medical_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.image_items is None:
            self.image_items = []
        if self.audio_items is None:
            self.audio_items = []
        if self.video_items is None:
            self.video_items = []
        if self.document_items is None:
            self.document_items = []
        if self.medical_context is None:
            self.medical_context = {}


class MultimodalRouter:
    """Routes content to appropriate processing pipelines"""
    
    def __init__(self):
        """Initialize multimodal router"""
        logger.info("🎯 Initializing Multimodal Content Router")
        
        self.phi_tokenizer = PHITokenizer()
        
        # Content type mappings
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
        self.audio_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.aac', '.opus'}
        self.video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.3gp'}
        self.document_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
        
        # Medical urgency keywords for priority detection
        self.emergency_keywords = {
            'sangre', 'hemorragia', 'unconsciente', 'desmayo', 'dolor_severo',
            'respirar', 'chest_pain', 'emergency', 'urgencia', 'ayuda'
        }
        
        self.urgent_keywords = {
            'dolor', 'infección', 'fiebre', 'roja', 'hinchado', 'infection',
            'fever', 'pain', 'swollen', 'wound', 'herida'
        }
        
        logger.info("✅ Multimodal Router initialized")
    
    def detect_content_type(self, file_path: Path) -> ContentType:
        """Detect content type from file extension and MIME type"""
        
        if not file_path or not file_path.exists():
            return ContentType.UNKNOWN
        
        # Get file extension
        extension = file_path.suffix.lower()
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # Classify by extension first
        if extension in self.image_extensions:
            return ContentType.IMAGE
        elif extension in self.audio_extensions:
            return ContentType.AUDIO
        elif extension in self.video_extensions:
            return ContentType.VIDEO
        elif extension in self.document_extensions:
            return ContentType.DOCUMENT
        
        # Fallback to MIME type
        if mime_type:
            if mime_type.startswith('image/'):
                return ContentType.IMAGE
            elif mime_type.startswith('audio/'):
                return ContentType.AUDIO
            elif mime_type.startswith('video/'):
                return ContentType.VIDEO
            elif mime_type.startswith('text/') or 'document' in mime_type:
                return ContentType.DOCUMENT
        
        return ContentType.UNKNOWN
    
    def detect_medical_priority(self, text_content: str) -> ProcessingPriority:
        """Detect medical priority from text content"""
        
        if not text_content:
            return ProcessingPriority.ROUTINE
        
        text_lower = text_content.lower()
        
        # Check for emergency keywords
        for keyword in self.emergency_keywords:
            if keyword in text_lower:
                return ProcessingPriority.EMERGENCY
        
        # Check for urgent keywords
        for keyword in self.urgent_keywords:
            if keyword in text_lower:
                return ProcessingPriority.URGENT
        
        return ProcessingPriority.ROUTINE
    
    async def parse_whatsapp_message(
        self,
        patient_id: str,
        patient_code: str,
        message_data: Dict[str, Any]
    ) -> MultimodalMessage:
        """Parse WhatsApp message into multimodal components"""
        
        logger.info(f"📱 Parsing WhatsApp message for patient {patient_code}")
        
        # Create multimodal message
        multimodal_msg = MultimodalMessage(
            patient_id=patient_id,
            patient_code=patient_code,
            timestamp=message_data.get('timestamp', ''),
            source="whatsapp"
        )
        
        # Extract text content
        if 'text' in message_data:
            multimodal_msg.text_content = message_data['text']
            
            # Detect medical priority from text
            priority = self.detect_medical_priority(multimodal_msg.text_content)
            logger.info(f"🚨 Medical priority detected: {priority.value}")
        
        # Process attachments/media
        if 'media' in message_data:
            media_items = message_data['media']
            if not isinstance(media_items, list):
                media_items = [media_items]
            
            for media in media_items:
                await self._process_media_item(media, multimodal_msg)
        
        # Process individual file if provided
        if 'file_path' in message_data:
            file_path = Path(message_data['file_path'])
            if file_path.exists():
                await self._process_file_item(file_path, multimodal_msg)
        
        logger.info(f"✅ Parsed message: {len(multimodal_msg.image_items)} images, "
                   f"{len(multimodal_msg.audio_items)} audio, "
                   f"{len(multimodal_msg.video_items)} video, "
                   f"{len(multimodal_msg.document_items)} docs")
        
        return multimodal_msg
    
    async def _process_media_item(self, media: Dict[str, Any], multimodal_msg: MultimodalMessage):
        """Process individual media item"""
        
        if 'file_path' in media:
            file_path = Path(media['file_path'])
            await self._process_file_item(file_path, multimodal_msg)
    
    async def _process_file_item(self, file_path: Path, multimodal_msg: MultimodalMessage):
        """Process individual file item"""
        
        content_type = self.detect_content_type(file_path)
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # Determine priority (inherit from text if urgent/emergency)
        priority = ProcessingPriority.ROUTINE
        if multimodal_msg.text_content:
            priority = self.detect_medical_priority(multimodal_msg.text_content)
        
        # Create content item
        content_item = ContentItem(
            content_type=content_type,
            content_data=file_path,
            mime_type=mime_type or 'application/octet-stream',
            file_path=file_path,
            priority=priority,
            metadata={
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
                'original_name': file_path.name
            }
        )
        
        # Route to appropriate list
        if content_type == ContentType.IMAGE:
            multimodal_msg.image_items.append(content_item)
            logger.info(f"📸 Added image: {file_path.name}")
        elif content_type == ContentType.AUDIO:
            multimodal_msg.audio_items.append(content_item)
            logger.info(f"🎵 Added audio: {file_path.name}")
        elif content_type == ContentType.VIDEO:
            multimodal_msg.video_items.append(content_item)
            logger.info(f"🎬 Added video: {file_path.name}")
        elif content_type == ContentType.DOCUMENT:
            multimodal_msg.document_items.append(content_item)
            logger.info(f"📄 Added document: {file_path.name}")
        else:
            logger.warning(f"❓ Unknown content type for: {file_path.name}")
    
    async def route_for_processing(self, multimodal_msg: MultimodalMessage) -> Dict[str, List[ContentItem]]:
        """Route content to appropriate processing pipelines"""
        
        logger.info(f"🎯 Routing content for processing - Patient: {multimodal_msg.patient_code}")
        
        processing_queues = {
            'text_analysis': [],
            'image_analysis': [],
            'audio_processing': [],
            'video_processing': [],
            'document_processing': []
        }
        
        # Route text content
        if multimodal_msg.text_content:
            text_item = ContentItem(
                content_type=ContentType.TEXT,
                content_data=multimodal_msg.text_content,
                mime_type='text/plain',
                priority=self.detect_medical_priority(multimodal_msg.text_content),
                metadata={
                    'length': len(multimodal_msg.text_content),
                    'language': 'es',  # Spanish default for Chilean patients
                    'medical_context': True
                }
            )
            processing_queues['text_analysis'].append(text_item)
        
        # Route media content
        processing_queues['image_analysis'].extend(multimodal_msg.image_items)
        processing_queues['audio_processing'].extend(multimodal_msg.audio_items)
        processing_queues['video_processing'].extend(multimodal_msg.video_items)
        processing_queues['document_processing'].extend(multimodal_msg.document_items)
        
        # Log routing summary
        for pipeline, items in processing_queues.items():
            if items:
                priorities = [item.priority.value for item in items]
                logger.info(f"📋 {pipeline}: {len(items)} items (priorities: {priorities})")
        
        return processing_queues
    
    def create_processing_manifest(self, multimodal_msg: MultimodalMessage) -> Dict[str, Any]:
        """Create processing manifest for audit and tracking"""
        
        manifest = {
            'patient_id': multimodal_msg.patient_id,
            'patient_code': multimodal_msg.patient_code,
            'timestamp': multimodal_msg.timestamp,
            'source': multimodal_msg.source,
            'content_summary': {
                'has_text': bool(multimodal_msg.text_content),
                'text_length': len(multimodal_msg.text_content) if multimodal_msg.text_content else 0,
                'image_count': len(multimodal_msg.image_items),
                'audio_count': len(multimodal_msg.audio_items),
                'video_count': len(multimodal_msg.video_items),
                'document_count': len(multimodal_msg.document_items)
            },
            'medical_priority': self.detect_medical_priority(multimodal_msg.text_content or '').value,
            'phi_tokenized': multimodal_msg.phi_tokenized,
            'processing_required': {
                'text_analysis': bool(multimodal_msg.text_content),
                'image_analysis': len(multimodal_msg.image_items) > 0,
                'audio_processing': len(multimodal_msg.audio_items) > 0,
                'video_processing': len(multimodal_msg.video_items) > 0,
                'document_processing': len(multimodal_msg.document_items) > 0
            }
        }
        
        return manifest


# Example usage and testing
async def test_bruce_wayne_multimodal():
    """Test multimodal routing with Bruce Wayne's data"""
    
    print("🦇 TESTING BRUCE WAYNE MULTIMODAL ROUTING")
    print("=" * 70)
    
    router = MultimodalRouter()
    
    # Simulate Bruce Wayne's WhatsApp message
    bruce_message = {
        'text': "Doctor, anoche me tomé los medicamentos pero aún me duele. La zona está más roja y tengo problemas para apoyar el talón",
        'timestamp': "2025-06-21T10:04:58Z",
        'file_path': "/Users/autonomos_dev/Projects/vigia/vigia_detect/data/input/bruce_wayne_talon.jpg"
    }
    
    # Parse message
    multimodal_msg = await router.parse_whatsapp_message(
        patient_id="ef50ad25-5ee6-4c6c-8e97-c94c348ce6d6",
        patient_code="+56961797823",
        message_data=bruce_message
    )
    
    print(f"📱 Parsed Bruce Wayne's message:")
    print(f"   📝 Text: {multimodal_msg.text_content[:50]}...")
    print(f"   📸 Images: {len(multimodal_msg.image_items)}")
    print(f"   🎵 Audio: {len(multimodal_msg.audio_items)}")
    print(f"   🎬 Video: {len(multimodal_msg.video_items)}")
    
    # Route for processing
    processing_queues = await router.route_for_processing(multimodal_msg)
    
    print(f"\n🎯 Processing Queues:")
    for pipeline, items in processing_queues.items():
        if items:
            print(f"   {pipeline}: {len(items)} items")
            for item in items:
                print(f"      - {item.content_type.value} ({item.priority.value})")
    
    # Create manifest
    manifest = router.create_processing_manifest(multimodal_msg)
    
    print(f"\n📋 Processing Manifest:")
    print(json.dumps(manifest, indent=2))
    
    return multimodal_msg, processing_queues, manifest


if __name__ == "__main__":
    asyncio.run(test_bruce_wayne_multimodal())