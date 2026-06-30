
import pytest
import numpy as np
from pathlib import Path
from src.cnnClassifier.components.feature_engineering import FeatureEngineering

class TestFeatureEngineering:
    def test_feature_extraction(self, tmp_path):
        """Test feature extraction pipeline"""
        # Create dummy config
        config = {
            'training_data': str(tmp_path),
            'features_dir': str(tmp_path / 'features'),
            'use_pca': False
        }
        
        # Create dummy image
        import cv2
        dummy_img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img_path = tmp_path / 'test.jpg'
        cv2.imwrite(str(img_path), dummy_img)
        
        # Test radiomic features
        fe = FeatureEngineering(config)
        features = fe.extract_radiomic_features(img_path)
        
        assert isinstance(features, dict)
        assert 'area' in features
        assert 'contrast' in features