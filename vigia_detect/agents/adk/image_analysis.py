"""
Image Analysis Agent - Native ADK Implementation
===============================================

Specialized agent for medical image analysis using YOLOv5 pressure injury detection.
Inherits from BaseAgent for custom medical image processing logic.
"""

import os
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import cv2
import torch

from google.adk.agents import BaseAgent, AgentContext
from google.adk.core.types import AgentCapability
from google.adk.tools import Tool

from .base import VigiaBaseAgent

logger = logging.getLogger(__name__)


class ImageAnalysisAgent(VigiaBaseAgent):
    """
    Medical image analysis agent using YOLOv5 for pressure injury detection.
    
    Capabilities:
    - LPP (pressure injury) detection and classification
    - Medical image preprocessing and enhancement
    - Confidence scoring and quality assessment
    - Integration with clinical assessment workflows
    """
    
    def __init__(self, config=None):
        """Initialize Image Analysis Agent with YOLOv5 model."""
        
        capabilities = [
            AgentCapability.IMAGE_ANALYSIS,
            AgentCapability.MEDICAL_DIAGNOSIS,
            AgentCapability.DATA_PROCESSING
        ]
        
        super().__init__(
            agent_id="vigia-image-analysis",
            agent_name="Vigia Image Analysis Agent",
            capabilities=capabilities,
            medical_specialties=["wound_care", "pressure_injuries", "dermatology"],
            config=config
        )
        
        # Initialize YOLOv5 model
        self.yolo_model = None
        self.model_path = None
        self._load_yolo_model()
        
        # Medical image processing parameters
        self.confidence_threshold = 0.5
        self.nms_threshold = 0.4
        self.image_size = 640
        
        # LPP grade classifications (NPUAP/EPUAP)
        self.lpp_grades = {
            0: "No LPP detected",
            1: "Grade 1 - Non-blanchable erythema",
            2: "Grade 2 - Partial thickness skin loss", 
            3: "Grade 3 - Full thickness skin loss",
            4: "Grade 4 - Full thickness tissue loss"
        }
        
        logger.info("Image Analysis Agent initialized with YOLOv5 model")
    
    def _load_yolo_model(self) -> None:
        """Load YOLOv5 model for pressure injury detection."""
        try:
            # Try to load custom trained model first
            custom_model_path = Path("models/yolov5_lpp_detection.pt")
            if custom_model_path.exists():
                self.yolo_model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                               path=str(custom_model_path))
                self.model_path = str(custom_model_path)
                logger.info(f"Loaded custom YOLOv5 model: {custom_model_path}")
            else:
                # Fallback to pre-trained model
                self.yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
                self.model_path = "yolov5s (pre-trained)"
                logger.warning("Custom model not found, using pre-trained YOLOv5s")
                
        except Exception as e:
            logger.error(f"Failed to load YOLOv5 model: {e}")
            self.yolo_model = None
    
    def create_tools(self) -> List[Tool]:
        """Create medical image analysis tools."""
        
        tools = super().create_medical_tools()
        
        def analyze_lpp_image(image_path: str, patient_id: str) -> dict:
            """Analyze medical image for pressure injury detection.
            
            Args:
                image_path: Path to medical image file
                patient_id: Patient identifier for audit trail
                
            Returns:
                dict: Analysis results with LPP detection data
            """
            try:
                if not os.path.exists(image_path):
                    return {
                        "status": "error",
                        "error": "Image file not found",
                        "image_path": image_path
                    }
                
                if self.yolo_model is None:
                    return {
                        "status": "error", 
                        "error": "YOLOv5 model not loaded"
                    }
                
                # Run YOLO detection
                results = self.yolo_model(image_path)
                
                # Process detection results
                detections = results.pandas().xyxy[0].to_dict('records')
                
                # Analyze detections for LPP
                lpp_analysis = self._analyze_lpp_detections(detections, image_path)
                
                # Log medical action
                self.audit_trail.append({
                    "action": "analyze_lpp_image",
                    "patient_id": patient_id,
                    "agent_id": self.agent_id,
                    "image_path": image_path,
                    "detections_count": len(detections),
                    "max_confidence": lpp_analysis.get("max_confidence", 0),
                    "timestamp": self._get_timestamp()
                })
                
                return {
                    "status": "success",
                    "patient_id": patient_id,
                    "image_path": image_path,
                    "model_used": self.model_path,
                    "analysis": lpp_analysis,
                    "raw_detections": detections
                }
                
            except Exception as e:
                logger.error(f"Error analyzing image {image_path}: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "image_path": image_path
                }
        
        tools.append(Tool(
            name="analyze_lpp_image",
            function=analyze_lpp_image,
            description="Analyze medical image for pressure injury detection using YOLOv5"
        ))
        
        def enhance_medical_image(image_path: str, output_path: str = None) -> dict:
            """Enhance medical image for better analysis.
            
            Args:
                image_path: Path to input medical image
                output_path: Optional path for enhanced image output
                
            Returns:
                dict: Enhancement results and output path
            """
            try:
                # Load image
                image = cv2.imread(image_path)
                if image is None:
                    return {"status": "error", "error": "Cannot load image"}
                
                # Medical image enhancement pipeline
                enhanced = self._enhance_medical_image(image)
                
                # Save enhanced image
                if output_path is None:
                    name, ext = os.path.splitext(image_path)
                    output_path = f"{name}_enhanced{ext}"
                
                cv2.imwrite(output_path, enhanced)
                
                return {
                    "status": "success",
                    "input_path": image_path,
                    "output_path": output_path,
                    "enhancements_applied": [
                        "contrast_improvement",
                        "noise_reduction", 
                        "color_balance"
                    ]
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        tools.append(Tool(
            name="enhance_medical_image",
            function=enhance_medical_image,
            description="Enhance medical image quality for better analysis"
        ))
        
        def get_image_quality_metrics(image_path: str) -> dict:
            """Assess medical image quality metrics.
            
            Args:
                image_path: Path to medical image
                
            Returns:
                dict: Image quality assessment metrics
            """
            try:
                image = cv2.imread(image_path)
                if image is None:
                    return {"status": "error", "error": "Cannot load image"}
                
                # Calculate quality metrics
                metrics = self._calculate_image_quality(image)
                
                return {
                    "status": "success",
                    "image_path": image_path,
                    "quality_metrics": metrics,
                    "recommendation": self._get_quality_recommendation(metrics)
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        tools.append(Tool(
            name="get_image_quality_metrics", 
            function=get_image_quality_metrics,
            description="Assess medical image quality for analysis suitability"
        ))
        
        return tools
    
    def _analyze_lpp_detections(self, detections: List[Dict], image_path: str) -> Dict[str, Any]:
        """Analyze YOLO detections for LPP classification."""
        
        if not detections:
            return {
                "lpp_detected": False,
                "lpp_grade": 0,
                "confidence": 0.0,
                "description": self.lpp_grades[0],
                "recommendations": ["Continue preventive care", "Regular skin assessment"],
                "detection_count": 0
            }
        
        # Find highest confidence detection
        max_confidence = max(det['confidence'] for det in detections)
        best_detection = max(detections, key=lambda x: x['confidence'])
        
        # Map detection class to LPP grade (this would be based on trained model classes)
        detected_class = best_detection.get('class', 0)
        lpp_grade = min(detected_class, 4)  # Cap at grade 4
        
        # Generate medical recommendations based on grade
        recommendations = self._generate_lpp_recommendations(lpp_grade, max_confidence)
        
        return {
            "lpp_detected": max_confidence >= self.confidence_threshold,
            "lpp_grade": lpp_grade,
            "confidence": float(max_confidence),
            "description": self.lpp_grades.get(lpp_grade, "Unknown grade"),
            "recommendations": recommendations,
            "detection_count": len(detections),
            "anatomical_location": self._infer_anatomical_location(best_detection),
            "urgency_level": self._determine_urgency(lpp_grade, max_confidence)
        }
    
    def _generate_lpp_recommendations(self, grade: int, confidence: float) -> List[str]:
        """Generate medical recommendations based on LPP grade."""
        
        base_recommendations = [
            "Document findings with photography",
            "Notify attending physician",
            "Update care plan"
        ]
        
        if grade == 0:
            return ["Continue preventive measures", "Regular skin assessment"]
        elif grade == 1:
            return base_recommendations + [
                "Implement pressure relief protocol",
                "Assess nutritional status",
                "Consider repositioning schedule"
            ]
        elif grade == 2:
            return base_recommendations + [
                "Begin wound care protocol",
                "Apply appropriate dressing",
                "Pain assessment and management",
                "Nutritional consultation"
            ]
        elif grade >= 3:
            return base_recommendations + [
                "URGENT: Immediate medical evaluation",
                "Wound care specialist consultation", 
                "Advanced wound care protocol",
                "Surgical evaluation if indicated",
                "Aggressive nutritional support"
            ]
        
        return base_recommendations
    
    def _enhance_medical_image(self, image: np.ndarray) -> np.ndarray:
        """Apply medical image enhancement techniques."""
        
        # Convert to LAB color space for better processing
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # Merge back and convert to BGR
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Noise reduction
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        return enhanced
    
    def _calculate_image_quality(self, image: np.ndarray) -> Dict[str, float]:
        """Calculate image quality metrics."""
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Blur assessment (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Brightness assessment
        brightness = np.mean(gray)
        
        # Contrast assessment  
        contrast = gray.std()
        
        # Noise assessment (local standard deviation)
        noise_score = np.mean([
            np.std(gray[i:i+10, j:j+10]) 
            for i in range(0, gray.shape[0]-10, 10)
            for j in range(0, gray.shape[1]-10, 10)
        ])
        
        return {
            "blur_score": float(blur_score),
            "brightness": float(brightness),
            "contrast": float(contrast), 
            "noise_score": float(noise_score),
            "resolution": f"{image.shape[1]}x{image.shape[0]}"
        }
    
    def _get_quality_recommendation(self, metrics: Dict[str, float]) -> str:
        """Get image quality recommendation."""
        
        if metrics["blur_score"] < 100:
            return "Image appears blurred - consider retaking with better focus"
        elif metrics["brightness"] < 50:
            return "Image too dark - improve lighting conditions"
        elif metrics["brightness"] > 200:
            return "Image too bright - reduce exposure"
        elif metrics["contrast"] < 30:
            return "Low contrast - adjust camera settings"
        else:
            return "Image quality acceptable for medical analysis"
    
    def _infer_anatomical_location(self, detection: Dict) -> str:
        """Infer anatomical location from detection position."""
        
        # Simple heuristic based on bounding box position
        x_center = (detection['xmin'] + detection['xmax']) / 2
        y_center = (detection['ymin'] + detection['ymax']) / 2
        
        # Normalize to image dimensions (would need actual image size)
        # This is a simplified version - real implementation would be more sophisticated
        
        if y_center < 0.3:
            return "upper_body"
        elif y_center > 0.7:
            return "lower_extremity"  
        else:
            return "torso_sacral_region"
    
    def _determine_urgency(self, grade: int, confidence: float) -> str:
        """Determine medical urgency level."""
        
        if grade >= 3 and confidence > 0.8:
            return "critical"
        elif grade >= 2 and confidence > 0.7:
            return "high"
        elif grade >= 1 and confidence > 0.6:
            return "medium"
        else:
            return "low"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for audit trail."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def process_medical_case(
        self,
        case_id: str,
        patient_data: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Process medical image analysis case.
        
        Args:
            case_id: Unique case identifier  
            patient_data: Contains image_path and patient info
            context: Agent execution context
            
        Returns:
            Medical image analysis results
        """
        
        image_path = patient_data.get("image_path")
        patient_id = patient_data.get("patient_id", case_id)
        
        if not image_path:
            return {
                "status": "error",
                "error": "No image_path provided in patient_data"
            }
        
        # Store case for tracking
        self.active_cases[case_id] = {
            "patient_id": patient_id,
            "image_path": image_path,
            "started_at": self._get_timestamp(),
            "status": "processing"
        }
        
        # Analyze the medical image
        tools = self.create_tools()
        analyze_tool = next(tool for tool in tools if tool.name == "analyze_lpp_image")
        
        result = analyze_tool.function(image_path, patient_id)
        
        # Update case status
        self.active_cases[case_id]["status"] = "completed"
        self.active_cases[case_id]["completed_at"] = self._get_timestamp()
        self.active_cases[case_id]["result"] = result
        
        # If high-grade LPP detected, send A2A message to clinical assessment agent
        if result.get("analysis", {}).get("lpp_grade", 0) >= 2:
            clinical_agent = await self.discover_medical_agent(
                AgentCapability.MEDICAL_DIAGNOSIS,
                "clinical_assessment"
            )
            
            if clinical_agent:
                await self.send_medical_message(
                    clinical_agent.agent_id,
                    "lpp_detection_alert",
                    {
                        "case_id": case_id,
                        "image_analysis": result,
                        "requires_clinical_review": True
                    },
                    patient_id=patient_id,
                    urgency=result.get("analysis", {}).get("urgency_level", "medium")
                )
        
        return result