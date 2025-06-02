# Vigía-Detect CLI

Herramienta de línea de comandos para procesamiento de imágenes de lesiones por presión mediante el sistema Vigía.

## Descripción

Este CLI permite procesar imágenes de lesiones por presión mediante un pipeline de visión computacional basado en YOLOv5-Wound. Detecta y clasifica LPP según su etapa (1-4) y puede guardar los resultados en una base de datos Supabase.

## Requisitos previos

- Python 3.8+
- PyTorch
- OpenCV
- Supabase Python SDK

## Instalación

1. Clonar el repositorio vigia-ulcer de YOLOv5-Wound:
   ```
   git clone https://github.com/calisma/pressure-ulcer
   ```

2. Configurar las variables de entorno:
   ```
   cp .env.example .env
   # Editar .env con las credenciales de Supabase
   ```

3. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

## Uso

### Procesar imágenes

```bash
python -m lpp_detect.cli.process_images --input ./data/input --output ./data/output
```

### Opciones

- `--input`, `-i`: Directorio de imágenes de entrada (default: ./data/input)
- `--output`, `-o`: Directorio para guardar resultados (default: ./data/output)
- `--patient-code`: Código único del paciente (opcional)
- `--confidence`: Umbral de confianza para detecciones (default: 0.25)
- `--save-db`: Guardar resultados en Supabase
- `--model`: Modelo YOLOv5 a utilizar (default: yolov5s)

### Ejemplos

1. Procesar directorio con configuración básica:
   ```
   python -m lpp_detect.cli.process_images
   ```

2. Procesar con paciente específico y guardar en BD:
   ```
   python -m lpp_detect.cli.process_images --patient-code PAT001 --save-db
   ```

3. Usar modelo más grande para mayor precisión:
   ```
   python -m lpp_detect.cli.process_images --model yolov5m --confidence 0.3
   ```

## Estructura de archivos

```
lpp_detect/
├── cli/
│   └── process_images.py      # CLI principal
├── cv_pipeline/
│   ├── detector.py            # Detector YOLOv5
│   └── preprocessor.py        # Preprocesador imágenes
├── db/
│   └── supabase_client.py     # Cliente Supabase
├── utils/
│   └── image_utils.py         # Utilidades imágenes
└── data/
    ├── input/                 # Directorio para imágenes entrada
    └── output/                # Directorio para resultados
```

## Notas importantes

- Las imágenes procesadas se guardan en el directorio de salida con anotaciones visuales
- Si se activa `--save-db`, los resultados se almacenan en la base de datos Supabase
- Para pacientes sin código especificado, se genera un código temporal
