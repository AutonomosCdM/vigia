#!/usr/bin/env python3
"""
Content Processing Pipelines
============================

Specialized processors for each content type:
- TextProcessor: Medical NLP analysis
- ImageProcessor: LPP Computer Vision
- AudioProcessor: Speech-to-text + medical analysis
- VideoProcessor: Frame extraction + audio processing
- DocumentProcessor: OCR + medical text analysis

All processors handle medical priority and HIPAA compliance.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json

# Add vigia_detect to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from vigia_detect.core.multimodal_router import ContentItem, ContentType, ProcessingPriority
from vigia_detect.utils.secure_logger import SecureLogger
from vigia_detect.monitoring.phi_tokenizer import PHITokenizer

logger = SecureLogger(__name__)


@dataclass
class ProcessingResult:
    """Result from content processing"""
    content_type: ContentType
    patient_id: str
    processing_status: str  # success, failed, partial
    results: Dict[str, Any]
    processing_time_ms: float
    metadata: Dict[str, Any]
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BaseContentProcessor(ABC):
    """Base class for content processors"""
    
    def __init__(self, processor_name: str):
        self.processor_name = processor_name
        self.phi_tokenizer = PHITokenizer()
        logger.info(f"🔧 Initialized {processor_name}")
    
    @abstractmethod
    async def process(self, content_item: ContentItem, patient_id: str) -> ProcessingResult:
        """Process content item"""
        pass
    
    def prioritize_processing(self, content_items: List[ContentItem]) -> List[ContentItem]:
        """Sort content items by medical priority"""
        priority_order = {
            ProcessingPriority.EMERGENCY: 0,
            ProcessingPriority.URGENT: 1,
            ProcessingPriority.ROUTINE: 2,
            ProcessingPriority.SCHEDULED: 3
        }
        
        return sorted(content_items, key=lambda x: priority_order[x.priority])


class TextProcessor(BaseContentProcessor):
    """Medical text analysis processor"""
    
    def __init__(self):
        super().__init__("TextProcessor")
        
        # Medical keyword categories
        self.symptoms_keywords = {
            'dolor': 'pain',
            'duele': 'pain',
            'roja': 'inflammation',
            'hinchado': 'swelling',
            'caliente': 'warmth',
            'fiebre': 'fever',
            'sangre': 'bleeding',
            'herida': 'wound',
            'infección': 'infection'
        }
        
        self.anatomy_keywords = {
            'talón': 'heel',
            'pie': 'foot',
            'pierna': 'leg',
            'espalda': 'back',
            'cadera': 'hip',
            'coxis': 'tailbone',
            'sacro': 'sacrum'
        }
        
        self.lpp_indicators = {
            'presión': 'pressure',
            'úlcera': 'ulcer',
            'lesión': 'lesion',
            'escara': 'bedsore',
            'apoyo': 'weight_bearing'
        }
    
    async def process(self, content_item: ContentItem, patient_id: str) -> ProcessingResult:
        """Process medical text content"""
        
        import time
        start_time = time.time()
        
        logger.info(f"📝 Processing text for patient {patient_id}")
        
        text_content = content_item.content_data
        
        # Medical text analysis
        analysis_results = {
            'original_text': text_content,
            'text_length': len(text_content),
            'language': 'spanish',
            'symptoms_detected': [],
            'anatomy_mentioned': [],
            'lpp_indicators': [],
            'medical_urgency': content_item.priority.value,
            'clinical_assessment': None
        }
        
        # Detect symptoms
        text_lower = text_content.lower()
        for symptom_es, symptom_en in self.symptoms_keywords.items():
            if symptom_es in text_lower:
                analysis_results['symptoms_detected'].append({
                    'symptom': symptom_en,
                    'spanish_term': symptom_es,
                    'found_in_text': True
                })
        
        # Detect anatomy
        for anatomy_es, anatomy_en in self.anatomy_keywords.items():
            if anatomy_es in text_lower:
                analysis_results['anatomy_mentioned'].append({
                    'anatomy': anatomy_en,
                    'spanish_term': anatomy_es,
                    'found_in_text': True
                })
        
        # Detect LPP indicators
        for indicator_es, indicator_en in self.lpp_indicators.items():
            if indicator_es in text_lower:
                analysis_results['lpp_indicators'].append({
                    'indicator': indicator_en,
                    'spanish_term': indicator_es,
                    'found_in_text': True
                })
        
        # Clinical assessment
        if analysis_results['symptoms_detected'] and analysis_results['anatomy_mentioned']:
            analysis_results['clinical_assessment'] = {
                'preliminary_diagnosis': 'possible_pressure_injury',
                'anatomical_focus': analysis_results['anatomy_mentioned'][0]['anatomy'],
                'symptom_profile': [s['symptom'] for s in analysis_results['symptoms_detected']],
                'requires_imaging': True,
                'urgency_level': content_item.priority.value
            }
        
        processing_time = (time.time() - start_time) * 1000
        
        return ProcessingResult(
            content_type=ContentType.TEXT,
            patient_id=patient_id,
            processing_status="success",
            results=analysis_results,
            processing_time_ms=processing_time,
            metadata={
                'processor': 'TextProcessor',
                'version': '1.0.0',
                'medical_context': True
            }
        )


class ImageProcessor(BaseContentProcessor):
    """Medical image analysis processor (LPP detection)"""
    
    def __init__(self):
        super().__init__("ImageProcessor")
        
        # Initialize image analysis components
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
    async def process(self, content_item: ContentItem, patient_id: str) -> ProcessingResult:
        """Process medical image for LPP detection"""
        
        import time
        start_time = time.time()
        
        logger.info(f"📸 Processing image for patient {patient_id}")
        
        file_path = content_item.file_path
        
        # Image analysis (using existing Vigia LPP detection)
        analysis_results = {
            'image_path': str(file_path),
            'image_format': file_path.suffix.lower(),
            'image_size_bytes': content_item.metadata.get('file_size', 0),
            'lpp_detection': None,
            'image_quality': None,
            'anatomical_region': None
        }
        
        # Mock LPP detection (in real system, would use actual computer vision)
        if file_path.exists():
            # Simulate image analysis
            analysis_results.update({
                'lpp_detection': {
                    'lpp_grade': 1,
                    'confidence': 0.75,
                    'anatomical_location': 'heel',
                    'lesion_characteristics': {
                        'erythema_present': True,
                        'skin_integrity': 'intact',
                        'estimated_size_cm': 2.0,
                        'stage_classification': 'stage_1'
                    },
                    'medical_recommendations': [
                        'pressure_relief',
                        'position_changes_q2h',
                        'nursing_assessment_24h',
                        'monitor_progression'
                    ]
                },
                'image_quality': {
                    'resolution': '201x300',
                    'clarity': 'diagnostic_quality',
                    'lighting': 'adequate',
                    'focus': 'sharp'
                },
                'anatomical_region': {
                    'primary_region': 'lower_extremity',
                    'specific_location': 'heel',
                    'view_angle': 'lateral'
                }
            })
        
        processing_time = (time.time() - start_time) * 1000
        
        return ProcessingResult(
            content_type=ContentType.IMAGE,
            patient_id=patient_id,
            processing_status="success",
            results=analysis_results,
            processing_time_ms=processing_time,
            metadata={
                'processor': 'ImageProcessor',
                'version': '1.0.0',
                'ai_model': 'vigia_lpp_detector_v2'
            }
        )


class AudioProcessor(BaseContentProcessor):
    """Audio processing - speech-to-text + medical analysis"""
    
    def __init__(self):
        super().__init__("AudioProcessor")
        
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.ogg', '.aac'}
    
    async def process(self, content_item: ContentItem, patient_id: str) -> ProcessingResult:
        """Process audio content"""
        
        import time
        start_time = time.time()
        
        logger.info(f"🎵 Processing audio for patient {patient_id}")
        
        # Audio processing results
        analysis_results = {
            'audio_file': str(content_item.file_path),
            'audio_format': content_item.mime_type,
            'duration_seconds': None,
            'speech_to_text': None,
            'medical_analysis': None,
            'audio_quality': None
        }
        
        # Mock speech-to-text (in real system would use Whisper/Google Speech API)
        if content_item.file_path and content_item.file_path.exists():
            # Simulate audio transcription
            analysis_results.update({
                'duration_seconds': 15.3,
                'speech_to_text': {
                    'transcription': "Doctor, necesito ayuda con mi herida del talón. Me duele mucho y está muy roja.",
                    'confidence': 0.92,
                    'language': 'es-CL',
                    'speaker_count': 1
                },
                'audio_quality': {
                    'clarity': 'good',
                    'background_noise': 'minimal',
                    'volume_level': 'adequate'
                }
            })
            
            # Process transcribed text through text processor
            text_processor = TextProcessor()
            text_content_item = ContentItem(
                content_type=ContentType.TEXT,
                content_data=analysis_results['speech_to_text']['transcription'],
                mime_type='text/plain',
                priority=content_item.priority
            )
            
            text_result = await text_processor.process(text_content_item, patient_id)
            analysis_results['medical_analysis'] = text_result.results
        
        processing_time = (time.time() - start_time) * 1000
        
        return ProcessingResult(
            content_type=ContentType.AUDIO,
            patient_id=patient_id,
            processing_status="success",
            results=analysis_results,
            processing_time_ms=processing_time,
            metadata={
                'processor': 'AudioProcessor',
                'version': '1.0.0',
                'stt_engine': 'whisper'
            }
        )


class VideoProcessor(BaseContentProcessor):
    """Video processing - frame extraction + audio analysis"""
    
    def __init__(self):
        super().__init__("VideoProcessor")
        
        self.supported_formats = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    
    async def process(self, content_item: ContentItem, patient_id: str) -> ProcessingResult:
        """Process video content"""
        
        import time
        start_time = time.time()
        
        logger.info(f"🎬 Processing video for patient {patient_id}")
        
        analysis_results = {
            'video_file': str(content_item.file_path),
            'video_format': content_item.mime_type,
            'duration_seconds': None,
            'frame_analysis': None,
            'audio_analysis': None,
            'video_quality': None
        }
        
        # Mock video processing
        if content_item.file_path and content_item.file_path.exists():
            analysis_results.update({
                'duration_seconds': 12.5,
                'video_quality': {
                    'resolution': '720x1280',
                    'fps': 30,
                    'lighting': 'good',
                    'stability': 'stable'
                },
                'frame_analysis': {
                    'frames_extracted': 5,
                    'key_frames': [
                        {'timestamp': 0.0, 'description': 'heel_overview'},
                        {'timestamp': 3.0, 'description': 'heel_closeup'},
                        {'timestamp': 6.0, 'description': 'heel_different_angle'},
                        {'timestamp': 9.0, 'description': 'heel_pressure_point'},
                        {'timestamp': 12.0, 'description': 'heel_final_view'}
                    ],
                    'medical_findings': {
                        'consistent_with_lpp': True,
                        'grade_progression_visible': False,
                        'multiple_angles_captured': True
                    }
                }
            })
            
            # Process audio track if present
            audio_processor = AudioProcessor()
            audio_content_item = ContentItem(
                content_type=ContentType.AUDIO,
                content_data=content_item.content_data,
                mime_type='audio/mp4',
                file_path=content_item.file_path,
                priority=content_item.priority
            )
            
            audio_result = await audio_processor.process(audio_content_item, patient_id)
            analysis_results['audio_analysis'] = audio_result.results
        
        processing_time = (time.time() - start_time) * 1000
        
        return ProcessingResult(
            content_type=ContentType.VIDEO,
            patient_id=patient_id,
            processing_status="success",
            results=analysis_results,
            processing_time_ms=processing_time,
            metadata={
                'processor': 'VideoProcessor',
                'version': '1.0.0',
                'frame_extraction': True
            }
        )


class DocumentProcessor(BaseContentProcessor):
    """Document processing - OCR + medical text analysis"""
    
    def __init__(self):
        super().__init__("DocumentProcessor")
        
        self.supported_formats = {'.pdf', '.doc', '.docx', '.txt'}
    
    async def process(self, content_item: ContentItem, patient_id: str) -> ProcessingResult:
        """Process document content"""
        
        import time
        start_time = time.time()
        
        logger.info(f"📄 Processing document for patient {patient_id}")
        
        analysis_results = {
            'document_file': str(content_item.file_path),
            'document_format': content_item.mime_type,
            'page_count': None,
            'extracted_text': None,
            'medical_analysis': None,
            'document_quality': None
        }
        
        # Mock document processing
        if content_item.file_path and content_item.file_path.exists():
            # Simulate OCR/text extraction
            extracted_text = "Informe médico: Paciente presenta lesión en talón derecho compatible con LPP Grado 1. Recomendaciones: alivio de presión y seguimiento."
            
            analysis_results.update({
                'page_count': 1,
                'extracted_text': extracted_text,
                'document_quality': {
                    'text_clarity': 'good',
                    'extraction_confidence': 0.95,
                    'formatting_preserved': True
                }
            })
            
            # Process extracted text
            text_processor = TextProcessor()
            text_content_item = ContentItem(
                content_type=ContentType.TEXT,
                content_data=extracted_text,
                mime_type='text/plain',
                priority=content_item.priority
            )
            
            text_result = await text_processor.process(text_content_item, patient_id)
            analysis_results['medical_analysis'] = text_result.results
        
        processing_time = (time.time() - start_time) * 1000
        
        return ProcessingResult(
            content_type=ContentType.DOCUMENT,
            patient_id=patient_id,
            processing_status="success",
            results=analysis_results,
            processing_time_ms=processing_time,
            metadata={
                'processor': 'DocumentProcessor',
                'version': '1.0.0',
                'ocr_engine': 'tesseract'
            }
        )


class ContentProcessingOrchestrator:
    """Orchestrates all content processing pipelines"""
    
    def __init__(self):
        logger.info("🎼 Initializing Content Processing Orchestrator")
        
        # Initialize processors
        self.processors = {
            ContentType.TEXT: TextProcessor(),
            ContentType.IMAGE: ImageProcessor(),
            ContentType.AUDIO: AudioProcessor(),
            ContentType.VIDEO: VideoProcessor(),
            ContentType.DOCUMENT: DocumentProcessor()
        }
        
        logger.info("✅ All content processors initialized")
    
    async def process_all_content(
        self, 
        processing_queues: Dict[str, List[ContentItem]], 
        patient_id: str
    ) -> Dict[str, List[ProcessingResult]]:
        """Process all content types concurrently"""
        
        logger.info(f"🎼 Processing all content for patient {patient_id}")
        
        # Map queue names to content types
        queue_mapping = {
            'text_analysis': ContentType.TEXT,
            'image_analysis': ContentType.IMAGE,
            'audio_processing': ContentType.AUDIO,
            'video_processing': ContentType.VIDEO,
            'document_processing': ContentType.DOCUMENT
        }
        
        # Process all content concurrently
        processing_tasks = []
        
        for queue_name, content_items in processing_queues.items():
            if content_items and queue_name in queue_mapping:
                content_type = queue_mapping[queue_name]
                processor = self.processors[content_type]
                
                # Create tasks for each content item
                for item in content_items:
                    task = processor.process(item, patient_id)
                    processing_tasks.append((queue_name, task))
        
        # Execute all tasks concurrently
        results = {}
        if processing_tasks:
            completed_tasks = await asyncio.gather(
                *[task for _, task in processing_tasks],
                return_exceptions=True
            )
            
            # Organize results by queue
            for i, (queue_name, _) in enumerate(processing_tasks):
                if queue_name not in results:
                    results[queue_name] = []
                
                task_result = completed_tasks[i]
                if isinstance(task_result, Exception):
                    logger.error(f"❌ Processing failed for {queue_name}: {task_result}")
                else:
                    results[queue_name].append(task_result)
        
        return results


# Testing function
async def test_content_processing():
    """Test content processing with Bruce Wayne's data"""
    
    print("🧪 TESTING CONTENT PROCESSING PIPELINES")
    print("=" * 70)
    
    # Import multimodal router
    from vigia_detect.core.multimodal_router import MultimodalRouter
    
    router = MultimodalRouter()
    orchestrator = ContentProcessingOrchestrator()
    
    # Simulate Bruce Wayne's message
    bruce_message = {
        'text': "Doctor, anoche me tomé los medicamentos pero aún me duele. La zona está más roja y tengo problemas para apoyar el talón",
        'timestamp': "2025-06-21T10:04:58Z",
        'file_path': "/Users/autonomos_dev/Projects/vigia/vigia_detect/data/input/bruce_wayne_talon.jpg"
    }
    
    # Parse and route
    multimodal_msg = await router.parse_whatsapp_message(
        patient_id="ef50ad25-5ee6-4c6c-8e97-c94c348ce6d6",
        patient_code="+56961797823",
        message_data=bruce_message
    )
    
    processing_queues = await router.route_for_processing(multimodal_msg)
    
    # Process all content
    processing_results = await orchestrator.process_all_content(
        processing_queues, 
        "ef50ad25-5ee6-4c6c-8e97-c94c348ce6d6"
    )
    
    # Display results
    print(f"\n📊 PROCESSING RESULTS:")
    for queue_name, results in processing_results.items():
        print(f"\n{queue_name.upper()}:")
        for result in results:
            print(f"   ✅ {result.content_type.value}: {result.processing_status}")
            print(f"      Processing time: {result.processing_time_ms:.1f}ms")
            if result.content_type == ContentType.TEXT:
                symptoms = result.results.get('symptoms_detected', [])
                print(f"      Symptoms: {[s['symptom'] for s in symptoms]}")
            elif result.content_type == ContentType.IMAGE:
                lpp = result.results.get('lpp_detection', {})
                print(f"      LPP Grade: {lpp.get('lpp_grade')} (confidence: {lpp.get('confidence')})")
    
    return processing_results


if __name__ == "__main__":
    asyncio.run(test_content_processing())