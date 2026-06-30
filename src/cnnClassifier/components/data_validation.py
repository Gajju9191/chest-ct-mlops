
"""
Data validation component for DVC pipeline.
Validates image quality before training.
"""
import cv2
import numpy as np
from pathlib import Path
import pandas as pd
import logging

from cnnClassifier import logger

class DataValidator:
    def __init__(self, config):
        self.config = config
        self.min_image_size = config.get('min_image_size', [224, 224])
        self.blur_threshold = config.get('blur_threshold', 50)
        self.max_artifacts = config.get('max_artifacts', 0)
        self.validate_labels = config.get('validate_labels', True)
        
    def validate_image(self, image_path: Path) -> dict:
        """Validate a single image"""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return {'valid': False, 'reason': 'failed_to_load'}
            
            # Check image size
            h, w = img.shape[:2]
            if h < self.min_image_size[0] or w < self.min_image_size[1]:
                return {'valid': False, 'reason': 'incorrect_size'}
            
            # Check for blur
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            if variance < self.blur_threshold:
                return {'valid': False, 'reason': 'blurry_image'}
            
            # Check for artifacts (bright spots, lines, etc.)
            artifacts = self.detect_artifacts(gray)
            if artifacts > self.max_artifacts:
                return {'valid': False, 'reason': 'artifacts_detected'}
            
            # Check for correct channels (medical images should be grayscale)
            if len(img.shape) == 3 and img.shape[2] != 1 and img.shape[2] != 3:
                return {'valid': False, 'reason': 'incorrect_channels'}
            
            return {'valid': True, 'variance': variance}
            
        except Exception as e:
            logger.warning(f"Error validating {image_path}: {e}")
            return {'valid': False, 'reason': str(e)}
    
    def detect_artifacts(self, gray_img):
        """Detect artifacts in image"""
        # Simple artifact detection using edge detection
        edges = cv2.Canny(gray_img, 50, 150)
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.size
        
        # If more than 10% of pixels are edges, might have artifacts
        if edge_pixels / total_pixels > 0.1:
            return 1
        return 0
    
    def validate_dataset(self, data_path: Path) -> pd.DataFrame:
        """Validate all images in dataset"""
        results = []
        
        for class_dir in data_path.iterdir():
            if class_dir.is_dir():
                for img_path in class_dir.glob('*.[jp][pn][g]'):
                    result = self.validate_image(img_path)
                    result['image_path'] = str(img_path)
                    result['label'] = class_dir.name
                    results.append(result)
        
        df = pd.DataFrame(results)
        
        # Log statistics
        valid_count = df[df['valid'] == True].shape[0]
        total_count = df.shape[0]
        logger.info(f"Validation: {valid_count}/{total_count} images valid")
        
        if total_count > 0:
            logger.info(f"Valid ratio: {valid_count/total_count*100:.1f}%")
        
        # Save report
        output_dir = Path("artifacts/validation")
        output_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_dir / 'validation_report.csv', index=False)
        
        return df