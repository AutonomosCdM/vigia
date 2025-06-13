"""
MedHELM Metrics Implementation
=============================

Implements the standard metrics used in MedHELM evaluation.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, confusion_matrix
)
import time


@dataclass
class MetricResult:
    """Result of a metric evaluation."""
    name: str
    value: float
    confidence_interval: Optional[Tuple[float, float]] = None
    metadata: Optional[Dict[str, Any]] = None


class MedHELMMetrics:
    """Standard metrics for MedHELM evaluation."""
    
    @staticmethod
    def accuracy(y_true: List[Any], y_pred: List[Any]) -> MetricResult:
        """Calculate accuracy metric."""
        score = accuracy_score(y_true, y_pred)
        return MetricResult(
            name="accuracy",
            value=score,
            metadata={"n_samples": len(y_true)}
        )
    
    @staticmethod
    def f1_score(y_true: List[Any], y_pred: List[Any], 
                 average: str = 'weighted') -> MetricResult:
        """Calculate F1 score."""
        score = f1_score(y_true, y_pred, average=average)
        return MetricResult(
            name="f1_score",
            value=score,
            metadata={"average": average}
        )
    
    @staticmethod
    def clinical_relevance(predictions: List[Dict], 
                          ground_truth: List[Dict]) -> MetricResult:
        """
        Calculate clinical relevance score.
        
        Measures how well predictions align with clinical guidelines.
        """
        relevant_count = 0
        total = len(predictions)
        
        for pred, truth in zip(predictions, ground_truth):
            # Check if prediction includes required clinical elements
            if all(key in pred for key in ['diagnosis', 'confidence', 'evidence']):
                # Check if diagnosis matches and has evidence
                if (pred.get('diagnosis') == truth.get('diagnosis') and
                    pred.get('evidence') is not None):
                    relevant_count += 1
                    
        score = relevant_count / total if total > 0 else 0
        
        return MetricResult(
            name="clinical_relevance",
            value=score,
            metadata={"relevant_predictions": relevant_count, "total": total}
        )
    
    @staticmethod
    def guideline_adherence(decisions: List[Dict], 
                           guidelines: List[str]) -> MetricResult:
        """
        Measure adherence to clinical guidelines.
        
        Specific to Vigía's NPUAP/EPUAP compliance.
        """
        adherent_count = 0
        total = len(decisions)
        
        for decision in decisions:
            # Check if decision references guidelines
            references = decision.get('references', [])
            evidence_level = decision.get('evidence_level', '')
            
            if references and evidence_level in ['A', 'B', 'C']:
                # Check if any reference matches known guidelines
                if any(guide in str(references) for guide in guidelines):
                    adherent_count += 1
                    
        score = adherent_count / total if total > 0 else 0
        
        return MetricResult(
            name="guideline_adherence",
            value=score,
            metadata={
                "adherent_decisions": adherent_count,
                "total": total,
                "guidelines_checked": guidelines
            }
        )
    
    @staticmethod
    def response_time(start_times: List[float], 
                     end_times: List[float]) -> MetricResult:
        """Measure average response time in seconds."""
        if len(start_times) != len(end_times):
            raise ValueError("Start and end times must have same length")
            
        response_times = [end - start for start, end in zip(start_times, end_times)]
        avg_time = np.mean(response_times)
        
        return MetricResult(
            name="response_time",
            value=avg_time,
            confidence_interval=(np.percentile(response_times, 5), 
                               np.percentile(response_times, 95)),
            metadata={
                "unit": "seconds",
                "median": np.median(response_times),
                "std": np.std(response_times)
            }
        )
    
    @staticmethod
    def sensitivity_specificity(y_true: List[int], 
                               y_pred: List[int]) -> Tuple[MetricResult, MetricResult]:
        """Calculate sensitivity and specificity."""
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        return (
            MetricResult(
                name="sensitivity",
                value=sensitivity,
                metadata={"true_positives": tp, "false_negatives": fn}
            ),
            MetricResult(
                name="specificity", 
                value=specificity,
                metadata={"true_negatives": tn, "false_positives": fp}
            )
        )
    
    @staticmethod
    def bert_score(predictions: List[str], 
                   references: List[str]) -> MetricResult:
        """
        Calculate BERTScore for text generation tasks.
        
        Note: This is a placeholder. Real implementation would use
        the bert_score library.
        """
        # Simplified implementation - real would use bert_score library
        # For now, return a mock score based on text similarity
        
        scores = []
        for pred, ref in zip(predictions, references):
            # Simple character overlap as proxy
            common = len(set(pred.lower().split()) & set(ref.lower().split()))
            total = max(len(pred.split()), len(ref.split()))
            score = common / total if total > 0 else 0
            scores.append(score)
            
        avg_score = np.mean(scores)
        
        return MetricResult(
            name="bert_score",
            value=avg_score,
            metadata={
                "note": "Simplified implementation - use bert_score library for production"
            }
        )
    
    @staticmethod
    def readability_score(texts: List[str]) -> MetricResult:
        """
        Calculate readability score for patient communication.
        
        Uses Flesch Reading Ease formula.
        """
        scores = []
        
        for text in texts:
            # Count sentences (simple approximation)
            sentences = text.count('.') + text.count('!') + text.count('?')
            sentences = max(1, sentences)
            
            # Count words
            words = len(text.split())
            
            # Count syllables (simple approximation)
            syllables = sum(len(word) > 3 for word in text.split()) * 2 + words
            
            # Flesch Reading Ease formula
            if words > 0:
                score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
                score = max(0, min(100, score))  # Clamp to 0-100
            else:
                score = 0
                
            scores.append(score)
            
        avg_score = np.mean(scores)
        
        return MetricResult(
            name="readability_score",
            value=avg_score,
            metadata={
                "scale": "Flesch Reading Ease (0-100, higher is easier)",
                "interpretation": {
                    "90-100": "Very Easy",
                    "80-89": "Easy", 
                    "70-79": "Fairly Easy",
                    "60-69": "Standard",
                    "50-59": "Fairly Difficult",
                    "30-49": "Difficult",
                    "0-29": "Very Difficult"
                }
            }
        )
    
    @staticmethod
    def medical_accuracy_vigía(detections: List[Dict]) -> MetricResult:
        """
        Vigía-specific medical accuracy metric.
        
        Measures LPP detection accuracy with clinical relevance.
        """
        correct = 0
        total = len(detections)
        
        for detection in detections:
            # Check if detection has required medical fields
            if all(key in detection for key in ['lpp_detected', 'grade', 'confidence']):
                # High confidence correct detections
                if detection['confidence'] > 0.7 and detection['clinical_validation']:
                    correct += 1
                    
        accuracy = correct / total if total > 0 else 0
        
        return MetricResult(
            name="medical_accuracy_vigía",
            value=accuracy,
            metadata={
                "lpp_specific": True,
                "confidence_threshold": 0.7,
                "validated_detections": correct
            }
        )