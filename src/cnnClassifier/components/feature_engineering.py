"""
Feature engineering component for DVC pipeline.
Extracts radiomic and deep features from CT scans.
"""
import numpy as np
import pandas as pd
import cv2
import joblib
import tensorflow as tf
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from skimage.feature import graycomatrix, graycoprops
import mlflow
import logging
import json

from cnnClassifier import logger

class FeatureEngineering:
    def __init__(self, config):
        self.config = config
        self.scaler = StandardScaler()
        self.pca = None
        self.feature_names = []
        
    def get_base_model(self):
        """Load pre-trained model for deep feature extraction"""
        if not hasattr(self, 'base_model'):
            self.base_model = tf.keras.applications.MobileNetV2(
                weights='imagenet',
                include_top=False,
                pooling='avg'
            )
        return self.base_model
    
    def extract_radiomic_features(self, image_path: Path) -> dict:
        """Extract radiomic features from a single image"""
        try:
            img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                return {}
            
            features = {}
            
            # Shape features
            binary = (img > 0).astype(np.uint8)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                largest = max(contours, key=cv2.contourArea)
                features['area'] = cv2.contourArea(largest)
                features['perimeter'] = cv2.arcLength(largest, True)
                features['compactness'] = (4 * np.pi * features['area']) / (features['perimeter']**2 + 1e-10)
            else:
                features['area'] = 0
                features['perimeter'] = 0
                features['compactness'] = 0
            
            # Intensity features
            non_zero = img[img > 0]
            if len(non_zero) > 0:
                features['mean_intensity'] = np.mean(non_zero)
                features['std_intensity'] = np.std(non_zero)
                features['skew'] = pd.Series(non_zero).skew()
                features['kurtosis'] = pd.Series(non_zero).kurtosis()
            else:
                features['mean_intensity'] = 0
                features['std_intensity'] = 0
                features['skew'] = 0
                features['kurtosis'] = 0
            
            # Texture features (GLCM)
            try:
                glcm = graycomatrix(img, distances=[1], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4],
                                  levels=256, symmetric=True)
                features['contrast'] = np.mean(graycoprops(glcm, 'contrast'))
                features['energy'] = np.mean(graycoprops(glcm, 'energy'))
                features['homogeneity'] = np.mean(graycoprops(glcm, 'homogeneity'))
                features['correlation'] = np.mean(graycoprops(glcm, 'correlation'))
            except:
                features['contrast'] = 0
                features['energy'] = 0
                features['homogeneity'] = 0
                features['correlation'] = 0
            
            return features
            
        except Exception as e:
            logger.warning(f"Error extracting radiomic features: {e}")
            return {}
    
    def extract_deep_features(self, image_path: Path) -> np.ndarray:
        """Extract deep features using pre-trained model"""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return None
            
            img = cv2.resize(img, (224, 224))
            img = tf.keras.applications.mobilenet_v2.preprocess_input(img)
            img = np.expand_dims(img, axis=0)
            
            model = self.get_base_model()
            features = model.predict(img, verbose=0).flatten()
            return features
            
        except Exception as e:
            logger.warning(f"Error extracting deep features: {e}")
            return None
    
    def build_feature_matrix(self, data_path: Path) -> tuple:
        """Build feature matrix from all images"""
        image_paths = []
        labels = []
        
        # Collect all images
        for class_dir in data_path.iterdir():
            if class_dir.is_dir():
                for img_path in class_dir.glob('*.[jp][pn][g]'):
                    image_paths.append(img_path)
                    labels.append(class_dir.name)
        
        logger.info(f"Found {len(image_paths)} images")
        
        # Extract features
        all_features = []
        metadata = []
        
        for img_path in image_paths:
            # Deep features
            deep = self.extract_deep_features(img_path)
            if deep is None:
                continue
            
            # Radiomic features
            radio = self.extract_radiomic_features(img_path)
            
            # Combine
            combined = np.concatenate([deep, list(radio.values())])
            all_features.append(combined)
            
            metadata.append({
                'image_id': img_path.stem,
                'path': str(img_path),
                'label': img_path.parent.name
            })
        
        # Convert to DataFrame
        feature_names = [f'deep_{i}' for i in range(deep.shape[0])]
        feature_names.extend(list(radio.keys()))
        self.feature_names = feature_names
        
        feature_df = pd.DataFrame(all_features, columns=feature_names)
        metadata_df = pd.DataFrame(metadata)
        
        logger.info(f"Extracted {len(feature_names)} features from {len(feature_df)} images")
        
        return feature_df, metadata_df
    
    def scale_features(self, feature_df: pd.DataFrame) -> pd.DataFrame:
        """Scale features using StandardScaler"""
        scaled = self.scaler.fit_transform(feature_df)
        return pd.DataFrame(scaled, columns=feature_df.columns)
    
    def reduce_dimensions(self, feature_df: pd.DataFrame) -> pd.DataFrame:
        """Apply PCA for dimensionality reduction"""
        if self.config.use_pca:
            self.pca = PCA(n_components=self.config.pca_components)
            reduced = self.pca.fit_transform(feature_df)
            logger.info(f"PCA reduced dimensions from {feature_df.shape[1]} to {reduced.shape[1]}")
            logger.info(f"Explained variance: {self.pca.explained_variance_ratio_.sum():.2%}")
            return pd.DataFrame(reduced, columns=[f'pca_{i}' for i in range(reduced.shape[1])])
        return feature_df
    
    def run(self):
        """Run the full feature engineering pipeline"""
        logger.info("Starting feature engineering...")
        
        # ✅ FIXED: Direct attribute access instead of .get()
        data_path = Path(self.config.training_data)
        
        if not data_path.exists():
            raise FileNotFoundError(f"Training data not found: {data_path}")
        
        logger.info(f"Using data from: {data_path}")
        
        # Build feature matrix
        feature_df, metadata_df = self.build_feature_matrix(data_path)
        
        # Scale features
        feature_df_scaled = self.scale_features(feature_df)
        
        # Reduce dimensions
        feature_df_final = self.reduce_dimensions(feature_df_scaled)
        
        # Save features
        output_dir = Path(self.config.root_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        feature_df_final.to_csv(self.config.features_file, index=False)
        metadata_df.to_csv(self.config.metadata_file, index=False)
        
        # Save scaler and PCA
        joblib.dump(self.scaler, self.config.scaler_file)
        if self.pca:
            joblib.dump(self.pca, self.config.pca_file)
        
        # Save feature stats
        stats = {
            'num_features': feature_df_final.shape[1],
            'num_samples': feature_df_final.shape[0],
            'use_pca': self.config.use_pca,
            'explained_variance': self.pca.explained_variance_ratio_.sum() if self.pca else 1.0
        }
        with open('artifacts/feature_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Log to MLflow
        try:
            with mlflow.start_run(run_name="feature_engineering"):
                mlflow.log_params(stats)
                mlflow.log_metric('feature_count', feature_df_final.shape[1])
        except:
            pass
        
        logger.info("Feature engineering completed!")
        return feature_df_final