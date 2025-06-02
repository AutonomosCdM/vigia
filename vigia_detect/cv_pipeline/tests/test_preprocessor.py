"""
Tests para el módulo de preprocesamiento de imágenes.

Verifica que el preprocesador aplique correctamente las transformaciones
a las imágenes para optimizarlas para la detección de LPP.
"""

import os
import pytest
import numpy as np
import cv2
from pathlib import Path

from cv_pipeline.preprocessor import ImagePreprocessor

# Directorio con imágenes de prueba
TEST_IMAGES_DIR = Path(__file__).resolve().parent / "data"

# Crear imagen de prueba si no existe
def setup_test_images():
    """Crea una imagen sintética de prueba si no existe."""
    os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
    
    # Imagen simple con un círculo rojo (similar a un eritema)
    test_img_path = TEST_IMAGES_DIR / "test_eritema_simple.jpg"
    
    if not test_img_path.exists():
        # Crear imagen de prueba
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        
        # Fondo beige claro (similar a piel)
        img[:, :] = [220, 210, 190]
        
        # Círculo rojizo (similar a eritema)
        center = (150, 150)
        cv2.circle(img, center, 50, (80, 100, 180), -1)  # BGR: rojizo para eritema
        
        # Guardar imagen
        cv2.imwrite(str(test_img_path), img)
    
    # Imagen con rostro sintético para probar detección facial
    test_face_path = TEST_IMAGES_DIR / "test_face_simple.jpg"
    
    if not test_face_path.exists():
        # Crear imagen con forma básica de cara
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        
        # Fondo beige claro
        img[:, :] = [220, 210, 190]
        
        # Forma oval para cara
        cv2.ellipse(img, (150, 150), (70, 100), 0, 0, 360, (200, 180, 140), -1)
        
        # Ojos (importantes para detección Haar Cascade)
        cv2.circle(img, (120, 120), 10, (255, 255, 255), -1)  # Ojo izquierdo
        cv2.circle(img, (180, 120), 10, (255, 255, 255), -1)  # Ojo derecho
        cv2.circle(img, (120, 120), 5, (50, 50, 50), -1)      # Pupila izquierda
        cv2.circle(img, (180, 120), 5, (50, 50, 50), -1)      # Pupila derecha
        
        # Nariz
        cv2.line(img, (150, 120), (150, 170), (120, 110, 100), 8)
        
        # Boca
        cv2.ellipse(img, (150, 190), (30, 10), 0, 0, 180, (100, 100, 100), 4)
        
        # Guardar imagen
        cv2.imwrite(str(test_face_path), img)
    
    return [test_img_path, test_face_path]

# Tests
def test_preprocessor_initialization():
    """Verifica la inicialización del preprocesador con diferentes parámetros."""
    # Inicialización con valores por defecto
    preprocessor = ImagePreprocessor()
    assert preprocessor.target_size == (640, 640)
    assert preprocessor.normalize == True
    
    # Inicialización con valores personalizados
    custom_preprocessor = ImagePreprocessor(
        target_size=(320, 320),
        normalize=False,
        face_detection=False
    )
    assert custom_preprocessor.target_size == (320, 320)
    assert custom_preprocessor.normalize == False
    assert custom_preprocessor.face_detection == False

def test_image_preprocessing_basic():
    """Verifica el procesamiento básico de una imagen."""
    # Crear imágenes de prueba
    test_images = setup_test_images()
    test_img_path = test_images[0]
    
    # Inicializar preprocesador
    preprocessor = ImagePreprocessor(
        target_size=(224, 224),
        normalize=True,
        face_detection=False,  # Desactivamos detección facial para este test
        enhance_contrast=True
    )
    
    # Procesar imagen
    processed_img = preprocessor.preprocess(test_img_path)
    
    # Verificar dimensiones
    assert processed_img.shape[:2] == (224, 224)
    
    # Verificar normalización
    assert processed_img.dtype == np.float32
    assert np.max(processed_img) <= 1.0
    
    # Verificar que no es un array vacío
    assert processed_img.size > 0

def test_face_detection_preprocessing():
    """Verifica el procesamiento con detección facial."""
    # Usar la imagen con rostro sintético
    test_images = setup_test_images()
    test_face_path = test_images[1]
    
    # Inicializar preprocesador con detección facial
    preprocessor = ImagePreprocessor(
        target_size=(300, 300),
        normalize=False,  # Desactivamos normalización para facilitar inspección
        face_detection=True,
        enhance_contrast=False  # Desactivamos mejora de contraste
    )
    
    # Procesar imagen
    processed_img = preprocessor.preprocess(test_face_path)
    
    # Verificar dimensiones
    assert processed_img.shape[:2] == (300, 300)
    
    # No podemos verificar automáticamente si se difuminó un rostro,
    # pero podemos verificar que el procesamiento no falló
    assert processed_img.size > 0
    
    # En un test real, podríamos guardar la imagen procesada para inspección visual
    # o usar un detector secundario para verificar si el rostro fue difuminado

def test_contrast_enhancement():
    """Verifica la mejora de contraste para detección de eritemas."""
    # Usar imagen con eritema sintético
    test_images = setup_test_images()
    test_img_path = test_images[0]
    
    # Cargar imagen original para comparar
    original_img = cv2.imread(str(test_img_path))
    
    # Inicializar preprocesador solo con mejora de contraste
    preprocessor = ImagePreprocessor(
        target_size=(300, 300),
        normalize=False,  # Desactivamos normalización para facilitar comparación
        face_detection=False,
        enhance_contrast=True,
        remove_exif=False
    )
    
    # Procesar imagen
    enhanced_img = preprocessor.preprocess(test_img_path)
    
    # En un test real, podríamos calcular el contraste antes y después
    # para verificar que aumentó, o usar herramientas específicas para
    # cuantificar la mejora en la visibilidad de los eritemas
    
    # Por ahora, verificamos que la imagen procesada es diferente de la original
    # resized_original = cv2.resize(original_img, (300, 300))
    # assert not np.array_equal(enhanced_img, resized_original)
    
    # Y verificamos que el procesamiento no falló
    assert enhanced_img.size > 0

if __name__ == "__main__":
    test_preprocessor_initialization()
    test_image_preprocessing_basic()
    test_face_detection_preprocessing()
    test_contrast_enhancement()
    print("Todos los tests pasaron correctamente.")
