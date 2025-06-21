"""
Patient Image Viewer - Clinical Progress Tracking Interface
==========================================================

Web-based interface for viewing patient medical images and tracking progress:
- Chronological image timeline
- LPP progression visualization
- Clinical notes and assessments
- Secure image viewing with PHI protection
- Progress comparison tools
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import uvicorn

from ..storage.medical_image_storage import (
    MedicalImageStorage, AnatomicalRegion, ImageType,
    get_patient_progress, store_patient_image
)
from ..core.phi_tokenization_client import TokenizedPatient, get_patient_by_token
from ..utils.secure_logger import SecureLogger
from ..utils.audit_service import AuditService, AuditEventType, AuditSeverity

logger = SecureLogger("patient_image_viewer")

# FastAPI app for image viewer
app = FastAPI(
    title="Vigia Patient Image Viewer",
    description="Clinical progress tracking interface for medical images",
    version="1.0.0"
)

# Setup templates and static files
templates = Jinja2Templates(directory="vigia_detect/interfaces/templates")
app.mount("/static", StaticFiles(directory="vigia_detect/interfaces/static"), name="static")

# Initialize services
image_storage = MedicalImageStorage()
audit_service = AuditService()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard for patient image viewing"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Vigia - Medical Image Viewer",
        "current_page": "dashboard"
    })


@app.get("/patient/{token_id}/images", response_model=List[Dict[str, Any]])
async def get_patient_images_api(
    token_id: str,
    anatomical_region: Optional[str] = Query(None),
    image_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    """
    API endpoint to get patient images
    
    Args:
        token_id: Tokenized patient identifier (e.g., Batman token)
        anatomical_region: Filter by anatomical region
        image_type: Filter by image type
        limit: Maximum number of images
        
    Returns:
        List of patient image records
    """
    try:
        # Validate token and get patient info
        tokenized_patient = await get_patient_by_token(token_id)
        if not tokenized_patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Convert string filters to enums
        region_filter = AnatomicalRegion(anatomical_region) if anatomical_region else None
        type_filter = ImageType(image_type) if image_type else None
        
        # Get images
        image_records = await image_storage.get_patient_images(
            token_id=token_id,
            anatomical_region=region_filter,
            image_type=type_filter,
            limit=limit
        )
        
        # Convert to API response format
        images = []
        for record in image_records:
            images.append({
                "image_id": record.image_id,
                "filename": record.metadata.filename,
                "anatomical_region": record.metadata.anatomical_region.value,
                "image_type": record.metadata.image_type.value,
                "clinical_context": record.metadata.clinical_context,
                "dimensions": record.metadata.dimensions,
                "file_size": record.metadata.file_size,
                "processing_status": record.metadata.processing_status.value,
                "uploaded_at": record.uploaded_at.isoformat(),
                "uploaded_by": record.uploaded_by,
                "storage_url": record.metadata.storage_url,
                "thumbnail_url": f"/image/{record.image_id}/thumbnail"
            })
        
        # Audit log
        await audit_service.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            component="patient_image_viewer",
            action="patient_images_viewed",
            session_id=f"view_{token_id}",
            details={
                "token_id": token_id,
                "patient_alias": tokenized_patient.patient_alias,
                "image_count": len(images),
                "anatomical_region": anatomical_region or "all",
                "image_type": image_type or "all"
            }
        )
        
        return images
        
    except Exception as e:
        logger.error(f"Failed to get patient images: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve images")


@app.get("/patient/{token_id}/progress/{anatomical_region}")
async def get_progress_timeline_api(
    token_id: str,
    anatomical_region: str
):
    """
    API endpoint to get progress timeline for specific anatomical region
    
    Args:
        token_id: Tokenized patient identifier
        anatomical_region: Anatomical region to track
        
    Returns:
        Chronological progress timeline with images and analysis
    """
    try:
        # Validate token
        tokenized_patient = await get_patient_by_token(token_id)
        if not tokenized_patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get progress timeline
        timeline = await get_patient_progress(token_id, anatomical_region)
        
        # Audit log
        await audit_service.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            component="patient_image_viewer", 
            action="progress_timeline_viewed",
            session_id=f"progress_{token_id}",
            details={
                "token_id": token_id,
                "patient_alias": tokenized_patient.patient_alias,
                "anatomical_region": anatomical_region,
                "timeline_entries": len(timeline)
            }
        )
        
        return {
            "patient_alias": tokenized_patient.patient_alias,
            "anatomical_region": anatomical_region,
            "timeline": timeline,
            "summary": {
                "total_images": len(timeline),
                "date_range": {
                    "first": timeline[0]["date"] if timeline else None,
                    "last": timeline[-1]["date"] if timeline else None
                },
                "lpp_progression": _analyze_lpp_progression(timeline)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get progress timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve progress timeline")


@app.get("/patient/{token_id}/viewer", response_class=HTMLResponse)
async def patient_viewer(request: Request, token_id: str):
    """Patient image viewer interface"""
    try:
        # Validate token
        tokenized_patient = await get_patient_by_token(token_id)
        if not tokenized_patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return templates.TemplateResponse("patient_viewer.html", {
            "request": request,
            "title": f"Patient Images - {tokenized_patient.patient_alias}",
            "patient_alias": tokenized_patient.patient_alias,
            "token_id": token_id,
            "anatomical_regions": [region.value for region in AnatomicalRegion],
            "image_types": [img_type.value for img_type in ImageType]
        })
        
    except Exception as e:
        logger.error(f"Failed to load patient viewer: {e}")
        raise HTTPException(status_code=500, detail="Failed to load patient viewer")


@app.get("/image/{image_id}")
async def get_image(image_id: str):
    """Serve medical image file"""
    try:
        # Get image record from database
        image_record = await image_storage.db_client.query_single(
            table="medical_images",
            filters={"image_id": image_id}
        )
        
        if not image_record:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Construct file path
        storage_base = image_storage.storage_base_path
        image_path = storage_base / image_record["storage_url"]
        
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # Audit access
        await audit_service.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            component="patient_image_viewer",
            action="medical_image_accessed", 
            session_id=f"img_access_{image_id}",
            details={
                "image_id": image_id,
                "token_id": image_record["token_id"],
                "anatomical_region": image_record["anatomical_region"]
            }
        )
        
        return FileResponse(
            path=image_path,
            media_type=f"image/{image_record['image_format'].lower()}",
            filename=image_record["filename"]
        )
        
    except Exception as e:
        logger.error(f"Failed to serve image: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve image")


@app.get("/image/{image_id}/thumbnail")
async def get_image_thumbnail(image_id: str):
    """Serve medical image thumbnail"""
    try:
        # Construct thumbnail path
        storage_base = image_storage.storage_base_path
        thumbnail_path = storage_base / "thumbnails" / f"{image_id}_thumb.jpg"
        
        if not thumbnail_path.exists():
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        return FileResponse(
            path=thumbnail_path,
            media_type="image/jpeg"
        )
        
    except Exception as e:
        logger.error(f"Failed to serve thumbnail: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve thumbnail")


@app.get("/patients/search")
async def search_patients(
    alias: Optional[str] = Query(None),
    limit: int = Query(20, le=50)
):
    """Search for patients by alias (for testing with tokenized data)"""
    try:
        # Search in tokenized_patients table
        filters = {}
        if alias:
            # In production, this would be a more sophisticated search
            filters["patient_alias"] = alias
        
        patients = await image_storage.db_client.query(
            table="tokenized_patients",
            filters=filters,
            limit=limit
        )
        
        # Return patient summaries
        patient_summaries = []
        for patient in patients:
            # Get image count for this patient
            image_count_result = await image_storage.db_client.query(
                table="medical_images",
                filters={"token_id": patient["token_id"]},
                count_only=True
            )
            
            patient_summaries.append({
                "token_id": patient["token_id"],
                "patient_alias": patient["patient_alias"],
                "age_range": patient["age_range"],
                "gender_category": patient["gender_category"],
                "token_status": patient["token_status"],
                "image_count": len(image_count_result) if image_count_result else 0,
                "created_at": patient["token_created_at"]
            })
        
        return patient_summaries
        
    except Exception as e:
        logger.error(f"Failed to search patients: {e}")
        raise HTTPException(status_code=500, detail="Failed to search patients")


def _analyze_lpp_progression(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze LPP progression from timeline data"""
    progression = {
        "trend": "unknown",
        "grade_changes": [],
        "latest_grade": None,
        "improvement_detected": False,
        "deterioration_detected": False
    }
    
    if not timeline:
        return progression
    
    # Extract LPP grades over time
    grades = []
    for entry in timeline:
        if entry.get("lpp_detection") and entry["lpp_detection"].get("lpp_grade"):
            grades.append({
                "date": entry["date"],
                "grade": entry["lpp_detection"]["lpp_grade"]
            })
    
    if not grades:
        return progression
    
    # Analyze trend
    progression["latest_grade"] = grades[-1]["grade"]
    progression["grade_changes"] = grades
    
    if len(grades) > 1:
        # Compare first and last grades
        first_grade = grades[0]["grade"]
        last_grade = grades[-1]["grade"]
        
        if last_grade < first_grade:
            progression["trend"] = "improving"
            progression["improvement_detected"] = True
        elif last_grade > first_grade:
            progression["trend"] = "deteriorating"
            progression["deterioration_detected"] = True
        else:
            progression["trend"] = "stable"
    
    return progression


# HTML Templates (would be in separate files in production)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Vigia Medical Image Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
        .search-box { margin: 20px 0; padding: 10px; border: 1px solid #ddd; }
        .patient-card { border: 1px solid #ddd; margin: 10px; padding: 15px; border-radius: 5px; }
        .btn { background: #3498db; color: white; padding: 10px 15px; text-decoration: none; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Vigia Medical Image Viewer</h1>
        <p>Secure patient image tracking and progress monitoring</p>
    </div>
    
    <div class="search-box">
        <h2>Search Patients</h2>
        <input type="text" id="searchAlias" placeholder="Patient alias (e.g., Batman)" style="width: 300px; padding: 8px;">
        <button onclick="searchPatients()" class="btn">Search</button>
    </div>
    
    <div id="patientResults"></div>
    
    <script>
        async function searchPatients() {
            const alias = document.getElementById('searchAlias').value;
            const response = await fetch(`/patients/search?alias=${alias}`);
            const patients = await response.json();
            
            const resultsDiv = document.getElementById('patientResults');
            resultsDiv.innerHTML = '<h2>Search Results</h2>';
            
            patients.forEach(patient => {
                resultsDiv.innerHTML += `
                    <div class="patient-card">
                        <h3>🦸 ${patient.patient_alias}</h3>
                        <p><strong>Age Range:</strong> ${patient.age_range}</p>
                        <p><strong>Images:</strong> ${patient.image_count}</p>
                        <p><strong>Status:</strong> ${patient.token_status}</p>
                        <a href="/patient/${patient.token_id}/viewer" class="btn">View Images</a>
                    </div>
                `;
            });
        }
        
        // Load default patients on page load
        window.onload = () => searchPatients();
    </script>
</body>
</html>
"""

PATIENT_VIEWER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Patient Images - {{patient_alias}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
        .filters { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
        .image-card { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: white; }
        .image-card img { width: 100%; height: 200px; object-fit: cover; }
        .image-info { padding: 15px; }
        .progress-timeline { margin: 20px 0; }
        .timeline-entry { border-left: 3px solid #3498db; padding: 10px; margin: 10px 0; background: #f8f9fa; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Patient Images - {{patient_alias}}</h1>
        <p>Medical image tracking and progress monitoring</p>
    </div>
    
    <div class="filters">
        <label>Anatomical Region:</label>
        <select id="regionFilter" onchange="loadImages()">
            <option value="">All Regions</option>
            {% for region in anatomical_regions %}
            <option value="{{region}}">{{region.replace('_', ' ').title()}}</option>
            {% endfor %}
        </select>
        
        <label>Image Type:</label>
        <select id="typeFilter" onchange="loadImages()">
            <option value="">All Types</option>
            {% for img_type in image_types %}
            <option value="{{img_type}}">{{img_type.replace('_', ' ').title()}}</option>
            {% endfor %}
        </select>
        
        <button onclick="loadProgress()" style="background: #27ae60; color: white; padding: 8px 15px; border: none; border-radius: 3px;">Load Progress Timeline</button>
    </div>
    
    <div id="imageGrid" class="image-grid"></div>
    <div id="progressTimeline" class="progress-timeline"></div>
    
    <script>
        const tokenId = '{{token_id}}';
        
        async function loadImages() {
            const region = document.getElementById('regionFilter').value;
            const type = document.getElementById('typeFilter').value;
            
            let url = `/patient/${tokenId}/images?`;
            if (region) url += `anatomical_region=${region}&`;
            if (type) url += `image_type=${type}&`;
            
            const response = await fetch(url);
            const images = await response.json();
            
            const gridDiv = document.getElementById('imageGrid');
            gridDiv.innerHTML = '';
            
            images.forEach(image => {
                const statusColor = {
                    'pending': '#f39c12',
                    'processing': '#3498db', 
                    'completed': '#27ae60',
                    'failed': '#e74c3c'
                }[image.processing_status] || '#95a5a6';
                
                gridDiv.innerHTML += `
                    <div class="image-card">
                        <img src="${image.thumbnail_url}" alt="Medical Image" onclick="viewFullImage('${image.image_id}')">
                        <div class="image-info">
                            <h3>${image.anatomical_region.replace('_', ' ').toUpperCase()}</h3>
                            <p><strong>Type:</strong> ${image.image_type.replace('_', ' ')}</p>
                            <p><strong>Date:</strong> ${new Date(image.uploaded_at).toLocaleDateString()}</p>
                            <p><strong>Context:</strong> ${image.clinical_context}</p>
                            <p><strong>Status:</strong> <span style="color: ${statusColor}">●</span> ${image.processing_status}</p>
                            <p><strong>Size:</strong> ${image.dimensions} (${Math.round(image.file_size/1024)} KB)</p>
                        </div>
                    </div>
                `;
            });
        }
        
        async function loadProgress() {
            const region = document.getElementById('regionFilter').value || 'sacrum';
            
            const response = await fetch(`/patient/${tokenId}/progress/${region}`);
            const progressData = await response.json();
            
            const timelineDiv = document.getElementById('progressTimeline');
            timelineDiv.innerHTML = `
                <h2>📈 Progress Timeline - ${progressData.anatomical_region.toUpperCase()}</h2>
                <p><strong>Patient:</strong> ${progressData.patient_alias}</p>
                <p><strong>Total Images:</strong> ${progressData.summary.total_images}</p>
                <p><strong>Trend:</strong> ${progressData.summary.lpp_progression.trend.toUpperCase()}</p>
            `;
            
            progressData.timeline.forEach(entry => {
                const lppInfo = entry.lpp_detection ? 
                    `<strong>LPP Grade:</strong> ${entry.lpp_detection.lpp_grade} | <strong>Confidence:</strong> ${(entry.lpp_detection.confidence_score * 100).toFixed(1)}%` :
                    '<em>No LPP detection data</em>';
                
                timelineDiv.innerHTML += `
                    <div class="timeline-entry">
                        <h4>${new Date(entry.date).toLocaleDateString()} - ${entry.image_type.replace('_', ' ').toUpperCase()}</h4>
                        <p>${entry.clinical_context}</p>
                        <p>${lppInfo}</p>
                        <img src="${entry.thumbnail_url}" style="max-width: 150px; margin: 10px 0;">
                    </div>
                `;
            });
        }
        
        function viewFullImage(imageId) {
            window.open(`/image/${imageId}`, '_blank');
        }
        
        // Load images on page load
        window.onload = () => loadImages();
    </script>
</body>
</html>
"""

# Create template directory and save templates
def setup_templates():
    """Setup HTML templates for the viewer"""
    template_dir = Path("vigia_detect/interfaces/templates")
    template_dir.mkdir(parents=True, exist_ok=True)
    
    (template_dir / "dashboard.html").write_text(DASHBOARD_HTML)
    (template_dir / "patient_viewer.html").write_text(PATIENT_VIEWER_HTML)


if __name__ == "__main__":
    # Setup templates
    setup_templates()
    
    # Run the viewer server
    uvicorn.run(
        "vigia_detect.interfaces.patient_image_viewer:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )