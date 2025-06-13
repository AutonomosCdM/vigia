
# Roboflow Pressure Ulcer Dataset Download Instructions

## Automatic Download (Requires API Key)

1. Sign up at: https://roboflow.com/
2. Get your API key from: https://app.roboflow.com/settings/api
3. Run the following commands:

```bash
pip install roboflow

# Replace YOUR_API_KEY with your actual API key
python -c "
from roboflow import Roboflow
rf = Roboflow(api_key='YOUR_API_KEY')
project = rf.workspace('calisma').project('pressure-ulcer')
dataset = project.version(1).download('yolov5')
"
```

## Manual Download (No API Key Required)

1. Visit: https://universe.roboflow.com/calisma/pressure-ulcer/dataset/1
2. Click "Download Dataset"
3. Select "YOLOv5 PyTorch" format
4. Extract to: roboflow_pressure_ulcer

## Dataset Information

- **Images**: 1078 pressure ulcer images
- **Classes**: 5 classes
  -   • pressure-ulcer-stage-1
  • pressure-ulcer-stage-2
  • pressure-ulcer-stage-3
  • pressure-ulcer-stage-4
  • non-pressure-ulcer
- **Annotations**: YOLOv5-compatible format
- **Source**: Roboflow Universe (calisma workspace)

## After Download

The dataset will have this structure:
```
roboflow_pressure_ulcer/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
├── data.yaml
└── README.dataset.txt
```

Run the analysis tool after download:
```bash
python ../analyze_datasets.py roboflow
```
