"""
Prediction Core Module - Implementation of the argmax equation.

This module implements the core argmax prediction system:
    ŷ = argmax_{x ∈ C} S(x | c)

Where:
    - ŷ is the predicted outcome
    - C is the candidate space (all possible predictions)
    - S(x|c) is a scoring function that evaluates candidate x given context c
"""

from .candidate_space import CandidateSpace, Direction
from .argmax_engine import ArgmaxEngine
from .confidence_calculator import ConfidenceCalculator
from .model_trainer import ModelTrainer
from .model_storage import ModelStorage
from . import scoring

__all__ = [
    'CandidateSpace',
    'Direction',
    'ArgmaxEngine',
    'ConfidenceCalculator',
    'ModelTrainer',
    'ModelStorage',
    'scoring',
]
