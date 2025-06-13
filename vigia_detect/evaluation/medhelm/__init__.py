"""
MedHELM Evaluation Framework for Vigía
=====================================

This module implements the MedHELM evaluation framework for assessing
Vigía's medical AI capabilities against standardized benchmarks.

MedHELM covers 5 main categories:
1. Clinical Decision Support
2. Clinical Note Generation
3. Patient Communication
4. Administration & Workflow
5. Medical Research Assistance

Reference: https://arxiv.org/abs/2505.23802v2
"""

from .taxonomy import MedHELMTaxonomy
from .runner import MedHELMRunner
from .metrics import MedHELMMetrics
from .mapper import VigiaCapabilityMapper

__all__ = [
    'MedHELMTaxonomy',
    'MedHELMRunner', 
    'MedHELMMetrics',
    'VigiaCapabilityMapper'
]

__version__ = '0.1.0'