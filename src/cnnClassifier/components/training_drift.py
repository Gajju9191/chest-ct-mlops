
"""
Training drift detection component for DVC pipeline.
"""
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from pathlib import Path
import json
import mlflow
import logging

from cnnClassifier import logger

class TrainingDriftDetector:
    def __init__(self, config):
        self.config = config
        self.threshold = config.get('threshold', 0.05)
        self.reference_data = None
        
    def load_reference_data(self, reference_path: Path):
        """Load reference data for drift detection"""
        if reference_path.exists():
            self.reference_data = pd.read_csv(reference_path)
            logger.info(f"Loaded reference data: {reference_path}")
            return True
        else:
            logger.warning(f"Reference data not found: {reference_path}")
            return False
    
    def detect_drift(self, new_data_path: Path):
        """Detect drift in new features"""
        # Load new data
        new_data = pd.read_csv(new_data_path)
        
        # If no reference, use first batch as reference
        if self.reference_data is None:
            self.reference_data = new_data.copy()
            logger.info("No reference data - using first batch as reference")
            return self._create_report(new_data, [])
        
        # Check for drift
        results = []
        drift_features = []
        
        for feature in self.reference_data.columns:
            if feature not in new_data.columns:
                continue
            
            # KS test
            stat, p_value = ks_2samp(
                self.reference_data[feature].dropna(),
                new_data[feature].dropna()
            )
            
            drift_detected = p_value < self.threshold
            results.append({
                'feature': feature,
                'p_value': p_value,
                'statistic': stat,
                'drift_detected': drift_detected
            })
            
            if drift_detected:
                drift_features.append(feature)
        
        # Update reference
        self.reference_data = new_data.copy()
        
        # Log to MLflow
        try:
            with mlflow.start_run(run_name="training_drift"):
                drift_pct = len(drift_features) / len(results) * 100 if results else 0
                mlflow.log_metrics({
                    'drift_percentage': drift_pct,
                    'drifted_features': len(drift_features),
                    'total_features': len(results)
                })
                for result in results:
                    mlflow.log_metric(f"p_value_{result['feature']}", result['p_value'])
        except:
            pass
        
        return self._create_report(new_data, results)
    
    def _create_report(self, data, results):
        """Create drift report"""
        total_features = len(results)
        drifted_features = sum(1 for r in results if r['drift_detected'])
        drift_pct = (drifted_features / total_features) * 100 if total_features > 0 else 0
        
        return {
            'timestamp': str(pd.Timestamp.now()),
            'total_features': total_features,
            'drifted_features': drifted_features,
            'drift_percentage': drift_pct,
            'results': results,
            'drift_detected': drift_pct > 10,
            'recommendation': 'Retrain recommended' if drift_pct > 15 else 'Monitor'
        }
    
    def save_report(self, report, output_path: Path):
        """Save drift report to file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved drift report: {output_path}")