#!/usr/bin/env python3
"""
Dataset Analysis Script for Medical Image Analysis
Vigia Project - Pressure Ulcer Detection System

This script analyzes downloaded medical image datasets for LPP detection suitability.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import logging
from collections import defaultdict, Counter
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatasetAnalyzer:
    """Analyzes medical image datasets for suitability in LPP detection"""
    
    def __init__(self, base_dir: str = "./datasets"):
        self.base_dir = Path(base_dir)
        self.results = {}
        
    def analyze_image_properties(self, dataset_path: Path) -> Dict:
        """
        Analyze image properties (dimensions, formats, quality)
        
        Args:
            dataset_path: Path to dataset directory
            
        Returns:
            Dict with image analysis results
        """
        logger.info(f"Analyzing image properties for {dataset_path.name}...")
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        properties = {
            'total_images': 0,
            'dimensions': [],
            'formats': Counter(),
            'sizes_mb': [],
            'errors': []
        }
        
        # Limit analysis to first 1000 images for performance
        image_files = []
        for ext in image_extensions:
            image_files.extend(list(dataset_path.rglob(f"*{ext}")))
            image_files.extend(list(dataset_path.rglob(f"*{ext.upper()}")))
        
        # Limit to first 1000 for performance
        image_files = image_files[:1000]
        properties['total_images'] = len(image_files)
        
        for img_path in image_files:
            try:
                with Image.open(img_path) as img:
                    # Dimensions
                    properties['dimensions'].append(img.size)
                    
                    # Format
                    properties['formats'][img.format] += 1
                    
                    # File size
                    size_mb = img_path.stat().st_size / (1024 * 1024)
                    properties['sizes_mb'].append(size_mb)
                    
            except Exception as e:
                properties['errors'].append(f"{img_path.name}: {str(e)}")
        
        # Calculate statistics
        if properties['dimensions']:
            widths, heights = zip(*properties['dimensions'])
            properties['width_stats'] = {
                'mean': np.mean(widths),
                'std': np.std(widths),
                'min': min(widths),
                'max': max(widths)
            }
            properties['height_stats'] = {
                'mean': np.mean(heights),
                'std': np.std(heights),
                'min': min(heights),
                'max': max(heights)
            }
        
        if properties['sizes_mb']:
            properties['size_stats'] = {
                'mean': np.mean(properties['sizes_mb']),
                'std': np.std(properties['sizes_mb']),
                'min': min(properties['sizes_mb']),
                'max': max(properties['sizes_mb'])
            }
        
        return properties
    
    def analyze_dataset_structure(self, dataset_path: Path) -> Dict:
        """
        Analyze dataset folder structure and organization
        
        Args:
            dataset_path: Path to dataset directory
            
        Returns:
            Dict with structure analysis
        """
        logger.info(f"Analyzing dataset structure for {dataset_path.name}...")
        
        structure = {
            'total_directories': 0,
            'directory_tree': {},
            'file_distribution': {},
            'annotation_files': [],
            'metadata_files': []
        }
        
        # Count directories and build tree
        for item in dataset_path.rglob("*"):
            if item.is_dir():
                structure['total_directories'] += 1
                
                # Count files in each directory
                file_count = len([f for f in item.iterdir() if f.is_file()])
                relative_path = str(item.relative_to(dataset_path))
                structure['file_distribution'][relative_path] = file_count
        
        # Look for annotation files
        annotation_patterns = ['*.json', '*.xml', '*.csv', '*.txt', '*.yml', '*.yaml']
        for pattern in annotation_patterns:
            structure['annotation_files'].extend(list(dataset_path.rglob(pattern)))
        
        # Look for metadata files
        metadata_patterns = ['*metadata*', '*readme*', '*description*', '*info*']
        for pattern in metadata_patterns:
            structure['metadata_files'].extend(list(dataset_path.rglob(pattern)))
        
        return structure
    
    def analyze_labels_and_classes(self, dataset_path: Path) -> Dict:
        """
        Analyze labels and classification structure
        
        Args:
            dataset_path: Path to dataset directory
            
        Returns:
            Dict with label analysis
        """
        logger.info(f"Analyzing labels and classes for {dataset_path.name}...")
        
        labels = {
            'class_directories': [],
            'csv_labels': {},
            'json_annotations': {},
            'inferred_classes': set()
        }
        
        # Look for class-based directory structure
        potential_class_dirs = []
        for item in dataset_path.iterdir():
            if item.is_dir():
                # Check if directory name suggests a class
                dir_name = item.name.lower()
                if any(keyword in dir_name for keyword in 
                      ['stage', 'grade', 'class', 'type', 'category', 'ulcer', 'wound']):
                    potential_class_dirs.append(item)
                    labels['inferred_classes'].add(dir_name)
        
        labels['class_directories'] = potential_class_dirs
        
        # Analyze CSV files for labels
        for csv_file in dataset_path.rglob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                labels['csv_labels'][csv_file.name] = {
                    'columns': list(df.columns),
                    'shape': df.shape,
                    'sample_data': df.head().to_dict() if len(df) > 0 else {}
                }
                
                # Look for class/label columns
                for col in df.columns:
                    if any(keyword in col.lower() for keyword in 
                          ['class', 'label', 'category', 'stage', 'grade', 'type']):
                        unique_values = df[col].unique()
                        labels['inferred_classes'].update(str(v) for v in unique_values)
                        
            except Exception as e:
                logger.warning(f"Error reading CSV {csv_file}: {e}")
        
        # Analyze JSON files for annotations
        for json_file in dataset_path.rglob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    labels['json_annotations'][json_file.name] = {
                        'type': type(data).__name__,
                        'keys': list(data.keys()) if isinstance(data, dict) else 'Not dict',
                        'sample': str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                    }
            except Exception as e:
                logger.warning(f"Error reading JSON {json_file}: {e}")
        
        return labels
    
    def evaluate_lpp_suitability(self, dataset_name: str, analysis: Dict) -> Dict:
        """
        Evaluate dataset suitability for LPP detection
        
        Args:
            dataset_name: Name of the dataset
            analysis: Combined analysis results
            
        Returns:
            Dict with suitability assessment
        """
        logger.info(f"Evaluating LPP suitability for {dataset_name}...")
        
        suitability = {
            'overall_score': 0,
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # Image quality assessment
        if 'image_properties' in analysis:
            props = analysis['image_properties']
            
            # Resolution check
            if props.get('width_stats', {}).get('mean', 0) >= 224:
                suitability['strengths'].append("Adequate image resolution for deep learning")
                suitability['overall_score'] += 2
            else:
                suitability['weaknesses'].append("Low image resolution may limit model performance")
            
            # Dataset size check
            if props['total_images'] >= 1000:
                suitability['strengths'].append(f"Large dataset ({props['total_images']} images)")
                suitability['overall_score'] += 3
            elif props['total_images'] >= 500:
                suitability['strengths'].append(f"Medium dataset ({props['total_images']} images)")
                suitability['overall_score'] += 2
            else:
                suitability['weaknesses'].append(f"Small dataset ({props['total_images']} images)")
                suitability['overall_score'] += 1
        
        # Label structure assessment
        if 'labels' in analysis:
            labels = analysis['labels']
            
            # Check for pressure ulcer related classes
            lpp_keywords = ['ulcer', 'pressure', 'stage', 'grade', 'wound', 'lesion']
            has_lpp_classes = any(
                any(keyword in str(class_name).lower() for keyword in lpp_keywords)
                for class_name in labels['inferred_classes']
            )
            
            if has_lpp_classes:
                suitability['strengths'].append("Contains pressure ulcer related classifications")
                suitability['overall_score'] += 3
            else:
                suitability['weaknesses'].append("No clear pressure ulcer classifications found")
        
        # Annotation availability
        if 'structure' in analysis:
            struct = analysis['structure']
            
            if struct['annotation_files']:
                suitability['strengths'].append(f"Contains annotation files ({len(struct['annotation_files'])})")
                suitability['overall_score'] += 2
            else:
                suitability['weaknesses'].append("No annotation files found")
        
        # Generate recommendations based on dataset name and analysis
        if dataset_name.lower() == 'ham10000':
            suitability['recommendations'].extend([
                "Use for transfer learning - pre-train on skin lesions",
                "Fine-tune on pressure ulcer specific data",
                "Focus on feature extraction layers"
            ])
        elif dataset_name.lower() == 'piid':
            suitability['recommendations'].extend([
                "Primary dataset for pressure ulcer detection",
                "Use data augmentation to increase dataset size",
                "Implement stratified split to maintain class balance"
            ])
        elif dataset_name.lower() == 'isic':
            suitability['recommendations'].extend([
                "Use for general skin lesion understanding",
                "Extract features for transfer learning",
                "Compare performance with HAM10000"
            ])
        
        # Calculate final score (0-10 scale)
        suitability['overall_score'] = min(10, suitability['overall_score'])
        
        return suitability
    
    def generate_analysis_report(self, dataset_name: str) -> Dict:
        """
        Generate comprehensive analysis report for a dataset
        
        Args:
            dataset_name: Name of dataset to analyze
            
        Returns:
            Complete analysis report
        """
        dataset_path = self.base_dir / dataset_name
        
        if not dataset_path.exists():
            return {
                'error': f"Dataset {dataset_name} not found at {dataset_path}",
                'exists': False
            }
        
        logger.info(f"Generating analysis report for {dataset_name}...")
        
        analysis = {
            'dataset_name': dataset_name,
            'path': str(dataset_path),
            'exists': True,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        # Perform all analyses
        analysis['image_properties'] = self.analyze_image_properties(dataset_path)
        analysis['structure'] = self.analyze_dataset_structure(dataset_path)
        analysis['labels'] = self.analyze_labels_and_classes(dataset_path)
        analysis['suitability'] = self.evaluate_lpp_suitability(dataset_name, analysis)
        
        return analysis
    
    def create_visualization_report(self, analyses: Dict[str, Dict]) -> None:
        """
        Create visualizations comparing datasets
        
        Args:
            analyses: Dictionary of analysis results by dataset name
        """
        logger.info("Creating visualization report...")
        
        # Create plots directory
        plots_dir = self.base_dir / "analysis_plots"
        plots_dir.mkdir(exist_ok=True)
        
        # 1. Dataset size comparison
        plt.figure(figsize=(12, 8))
        
        dataset_names = []
        image_counts = []
        suitability_scores = []
        
        for name, analysis in analyses.items():
            if analysis.get('exists', False):
                dataset_names.append(name.upper())
                image_counts.append(analysis.get('image_properties', {}).get('total_images', 0))
                suitability_scores.append(analysis.get('suitability', {}).get('overall_score', 0))
        
        # Size comparison bar plot
        plt.subplot(2, 2, 1)
        plt.bar(dataset_names, image_counts, color=['skyblue', 'lightgreen', 'lightcoral'][:len(dataset_names)])
        plt.title('Dataset Size Comparison')
        plt.ylabel('Number of Images')
        plt.xticks(rotation=45)
        
        # Suitability scores
        plt.subplot(2, 2, 2)
        plt.bar(dataset_names, suitability_scores, color=['gold', 'silver', 'bronze'][:len(dataset_names)])
        plt.title('LPP Suitability Scores')
        plt.ylabel('Suitability Score (0-10)')
        plt.xticks(rotation=45)
        
        # Image resolution distribution (for first available dataset)
        for name, analysis in analyses.items():
            if analysis.get('exists', False) and 'image_properties' in analysis:
                props = analysis['image_properties']
                if props.get('dimensions'):
                    plt.subplot(2, 2, 3)
                    widths, heights = zip(*props['dimensions'][:100])  # Sample first 100
                    plt.scatter(widths, heights, alpha=0.6, label=name)
                    plt.xlabel('Width (pixels)')
                    plt.ylabel('Height (pixels)')
                    plt.title('Image Dimensions Distribution')
                    plt.legend()
                    break
        
        # File size distribution
        plt.subplot(2, 2, 4)
        for name, analysis in analyses.items():
            if analysis.get('exists', False) and 'image_properties' in analysis:
                props = analysis['image_properties']
                if props.get('sizes_mb'):
                    plt.hist(props['sizes_mb'][:100], alpha=0.7, label=name, bins=20)
        plt.xlabel('File Size (MB)')
        plt.ylabel('Frequency')
        plt.title('File Size Distribution')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'dataset_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualization saved to: {plots_dir / 'dataset_comparison.png'}")
    
    def analyze_all_datasets(self) -> None:
        """Analyze all available datasets and generate comprehensive report"""
        
        datasets = ['ham10000', 'isic', 'piid']
        all_analyses = {}
        
        for dataset in datasets:
            logger.info(f"\n{'='*60}")
            logger.info(f"ANALYZING DATASET: {dataset.upper()}")
            logger.info(f"{'='*60}")
            
            analysis = self.generate_analysis_report(dataset)
            all_analyses[dataset] = analysis
            
            # Print summary
            if analysis.get('exists', False):
                print(f"\n✅ {dataset.upper()} Analysis Complete:")
                
                # Image properties
                if 'image_properties' in analysis:
                    props = analysis['image_properties']
                    print(f"  📊 Images: {props['total_images']}")
                    if props.get('width_stats'):
                        print(f"  📐 Avg Resolution: {props['width_stats']['mean']:.0f}x{props['height_stats']['mean']:.0f}")
                    if props.get('size_stats'):
                        print(f"  💾 Avg Size: {props['size_stats']['mean']:.2f} MB")
                
                # Suitability
                if 'suitability' in analysis:
                    suit = analysis['suitability']
                    print(f"  🎯 LPP Suitability: {suit['overall_score']}/10")
                    print(f"  ✅ Strengths: {len(suit['strengths'])}")
                    print(f"  ⚠️  Weaknesses: {len(suit['weaknesses'])}")
            else:
                print(f"\n❌ {dataset.upper()}: {analysis.get('error', 'Not available')}")
        
        # Create visualizations
        self.create_visualization_report(all_analyses)
        
        # Save detailed results
        results_file = self.base_dir / "analysis_results.json"
        with open(results_file, 'w') as f:
            json.dump(all_analyses, f, indent=2, default=str)
        
        logger.info(f"\nDetailed analysis saved to: {results_file}")
        
        # Print final recommendations
        print(f"\n{'='*60}")
        print("FINAL RECOMMENDATIONS")
        print(f"{'='*60}")
        
        available_datasets = [name for name, analysis in all_analyses.items() 
                            if analysis.get('exists', False)]
        
        if available_datasets:
            print(f"✅ Available datasets: {', '.join(available_datasets)}")
            
            # Sort by suitability score
            sorted_datasets = sorted(
                available_datasets,
                key=lambda x: all_analyses[x].get('suitability', {}).get('overall_score', 0),
                reverse=True
            )
            
            print(f"🏆 Best for LPP: {sorted_datasets[0] if sorted_datasets else 'None'}")
            
            if 'piid' in available_datasets:
                print("💡 Strategy: Use PIID as primary, HAM10000 for transfer learning")
            elif 'ham10000' in available_datasets:
                print("💡 Strategy: Use HAM10000 for transfer learning, need specific LPP data")
            else:
                print("💡 Strategy: Download specific LPP datasets before proceeding")
        else:
            print("❌ No datasets available. Please download datasets first.")

def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        dataset_name = sys.argv[1]
    else:
        dataset_name = "all"
    
    analyzer = DatasetAnalyzer()
    
    if dataset_name == "all":
        analyzer.analyze_all_datasets()
    else:
        # Analyze specific dataset
        analysis = analyzer.generate_analysis_report(dataset_name)
        print(json.dumps(analysis, indent=2, default=str))

if __name__ == "__main__":
    main()