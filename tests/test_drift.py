
import pytest
import numpy as np
import pandas as pd
from src.cnnClassifier.components.training_drift import TrainingDriftDetector

class TestTrainingDrift:
    def test_drift_detection(self):
        """Test basic drift detection"""
        # Create reference data
        ref_data = pd.DataFrame({
            'feature1': np.random.normal(0, 1, 100),
            'feature2': np.random.normal(0, 1, 100)
        })
        
        # Create drifted data
        new_data = pd.DataFrame({
            'feature1': np.random.normal(2, 1, 100),  # Shifted
            'feature2': np.random.normal(0, 1, 100)
        })
        
        detector = TrainingDriftDetector({'threshold': 0.05})
        detector.reference_data = ref_data
        
        report = detector.detect_drift(new_data)
        
        assert 'drift_detected' in report
        assert 'drift_percentage' in report
        assert len(report['results']) == 2

    def test_no_drift(self):
        """Test no drift detection"""
        data = pd.DataFrame({
            'feature1': np.random.normal(0, 1, 100),
            'feature2': np.random.normal(0, 1, 100)
        })
        
        detector = TrainingDriftDetector({'threshold': 0.05})
        detector.reference_data = data
        
        report = detector.detect_drift(data)
        
        assert report['drift_percentage'] == 0
        assert all(not r['drift_detected'] for r in report['results'])