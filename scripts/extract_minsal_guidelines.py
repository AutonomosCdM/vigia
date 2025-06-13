#!/usr/bin/env python3
"""
Script para extraer información clave de documentos MINSAL LPP
"""

import PyPDF2
import re
import json
from pathlib import Path
from typing import Dict, List, Any

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae texto de un archivo PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    print(f"Error extrayendo página: {e}")
                    continue
            return text
    except Exception as e:
        print(f"Error leyendo PDF {pdf_path}: {e}")
        return ""

def extract_classification_info(text: str) -> Dict[str, List[str]]:
    """Extrae información de clasificación de LPP"""
    classification = {
        "grades": [],
        "descriptions": [],
        "characteristics": []
    }
    
    # Patrones para encontrar clasificaciones
    grade_patterns = [
        r'(estadio|etapa|grado|categoría|category)\s+(I|II|III|IV|1|2|3|4)',
        r'(grado|estadio)\s*(\d+)',
        r'(estadio|grado)\s*(uno|dos|tres|cuatro|I|II|III|IV)'
    ]
    
    for pattern in grade_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            context = text[max(0, match.start()-100):match.end()+200]
            classification["grades"].append(match.group())
            classification["descriptions"].append(context.strip())
    
    # Buscar características específicas
    characteristics_patterns = [
        r'eritema\s+no\s+blanqueable',
        r'pérdida\s+parcial.*espesor',
        r'pérdida\s+completa.*espesor',
        r'exposición.*hueso',
        r'necrosis',
        r'esfacelo'
    ]
    
    for pattern in characteristics_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            classification["characteristics"].append(match.group())
    
    return classification

def extract_prevention_measures(text: str) -> List[str]:
    """Extrae medidas preventivas mencionadas"""
    prevention = []
    
    prevention_patterns = [
        r'prevención[^.]*',
        r'medidas\s+preventivas[^.]*',
        r'reposicionamiento[^.]*',
        r'colchón[^.]*',
        r'superficie[^.]*presión[^.]*',
        r'cuidado\s+de\s+la\s+piel[^.]*',
        r'evaluación\s+del\s+riesgo[^.]*',
        r'escala\s+de\s+braden[^.]*'
    ]
    
    for pattern in prevention_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            prevention.append(match.group().strip())
    
    return list(set(prevention))  # Eliminar duplicados

def extract_treatment_recommendations(text: str) -> List[str]:
    """Extrae recomendaciones de tratamiento"""
    treatment = []
    
    treatment_patterns = [
        r'tratamiento[^.]*',
        r'curación[^.]*',
        r'apósito[^.]*',
        r'desbridamiento[^.]*',
        r'manejo\s+del\s+dolor[^.]*',
        r'antibiótico[^.]*',
        r'cicatrización[^.]*'
    ]
    
    for pattern in treatment_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            treatment.append(match.group().strip())
    
    return list(set(treatment))

def extract_risk_factors(text: str) -> List[str]:
    """Extrae factores de riesgo mencionados"""
    risk_factors = []
    
    risk_patterns = [
        r'factor[es]?\s+de\s+riesgo[^.]*',
        r'inmovilidad[^.]*',
        r'diabetes[^.]*',
        r'desnutrición[^.]*',
        r'edad\s+avanzada[^.]*',
        r'incontinencia[^.]*',
        r'presión[^.]*',
        r'fricción[^.]*',
        r'cizallamiento[^.]*'
    ]
    
    for pattern in risk_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            risk_factors.append(match.group().strip())
    
    return list(set(risk_factors))

def process_minsal_documents() -> Dict[str, Any]:
    """Procesa todos los documentos MINSAL descargados"""
    
    documents_info = {}
    pdf_directory = Path("vigia_detect/references/minsal")
    
    for pdf_file in pdf_directory.glob("*.pdf"):
        print(f"Procesando {pdf_file.name}...")
        
        text = extract_text_from_pdf(str(pdf_file))
        if not text:
            print(f"No se pudo extraer texto de {pdf_file.name}")
            continue
        
        # Extraer información estructurada
        classification = extract_classification_info(text)
        prevention = extract_prevention_measures(text)
        treatment = extract_treatment_recommendations(text)
        risk_factors = extract_risk_factors(text)
        
        documents_info[pdf_file.name] = {
            "file_path": str(pdf_file),
            "text_length": len(text),
            "classification": classification,
            "prevention_measures": prevention[:10],  # Limitar a 10 items más relevantes
            "treatment_recommendations": treatment[:10],
            "risk_factors": risk_factors[:10],
            "key_terms_found": {
                "lesiones_por_presion": len(re.findall(r'lesiones?\s+por\s+presión', text, re.IGNORECASE)),
                "ulceras_por_presion": len(re.findall(r'úlceras?\s+por\s+presión', text, re.IGNORECASE)),
                "prevention": len(re.findall(r'prevención', text, re.IGNORECASE)),
                "tratamiento": len(re.findall(r'tratamiento', text, re.IGNORECASE))
            }
        }
        
        print(f"✓ Procesado {pdf_file.name}: {len(text)} caracteres de texto")
    
    return documents_info

def save_extracted_info(info: Dict[str, Any]):
    """Guarda la información extraída en archivo JSON"""
    output_file = "vigia_detect/systems/config/minsal_extracted_info.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Información guardada en {output_file}")

def generate_summary_report(info: Dict[str, Any]):
    """Genera un reporte resumen de la información extraída"""
    print("\n" + "="*60)
    print("RESUMEN DE INFORMACIÓN EXTRAÍDA DE DOCUMENTOS MINSAL")
    print("="*60)
    
    total_docs = len(info)
    print(f"Total de documentos procesados: {total_docs}")
    
    for doc_name, doc_info in info.items():
        print(f"\n📄 {doc_name}")
        print(f"   Texto extraído: {doc_info['text_length']:,} caracteres")
        print(f"   Clasificaciones encontradas: {len(doc_info['classification']['grades'])}")
        print(f"   Medidas preventivas: {len(doc_info['prevention_measures'])}")
        print(f"   Recomendaciones tratamiento: {len(doc_info['treatment_recommendations'])}")
        print(f"   Factores de riesgo: {len(doc_info['risk_factors'])}")
        
        # Términos clave
        terms = doc_info['key_terms_found']
        print(f"   Términos clave: LPP({terms['lesiones_por_presion']}), UPP({terms['ulceras_por_presion']})")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("Iniciando extracción de información de documentos MINSAL...")
    
    extracted_info = process_minsal_documents()
    
    if extracted_info:
        save_extracted_info(extracted_info)
        generate_summary_report(extracted_info)
        print("\n✅ Extracción completada exitosamente")
    else:
        print("\n❌ No se pudo extraer información de ningún documento")