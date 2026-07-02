# src/cnnClassifier/components/model_trainer.py

import tensorflow as tf
import pandas as pd
import numpy as np
from pathlib import Path
from cnnClassifier import logger
from cnnClassifier.entity.config_entity import TrainingConfig

class Training:
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.X_train = None
        self.y_train = None
        self.X_val = None
        self.y_val = None

    def get_base_model(self):
        logger.info("Loading base model...")
        self.model = tf.keras.models.load_model(
            self.config.updated_base_model_path
        )

        # Re-compile with a NEW optimizer instance
        self.model.compile(
            optimizer=tf.keras.optimizers.SGD(
                learning_rate=self.config.params_learning_rate
            ),
            loss=tf.keras.losses.CategoricalCrossentropy(),
            metrics=["accuracy"],
        )
        logger.info("Base model loaded and re-compiled successfully!")

    def load_features(self):
        """Load features from CSV files"""
        logger.info("Loading features...")
        
        features_path = Path(self.config.training_data) / "features.csv"
        metadata_path = Path(self.config.training_data) / "metadata.csv"
        
        if not features_path.exists():
            raise FileNotFoundError(f"Features file not found: {features_path}")
        
        # Load features
        features_df = pd.read_csv(features_path)
        metadata_df = pd.read_csv(metadata_path)
        
        # Extract features and labels
        self.X = features_df.values
        
        # Convert labels to one-hot
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        y_encoded = le.fit_transform(metadata_df['label'])
        self.y = tf.keras.utils.to_categorical(y_encoded, num_classes=2)
        
        logger.info(f"Loaded {len(self.X)} samples with {self.X.shape[1]} features")
        return self.X, self.y

    def train_valid_generator(self):
        """Split features into train/validation sets"""
        logger.info("Splitting features into train/validation...")
        
        from sklearn.model_selection import train_test_split
        
        # Split data
        self.X_train, self.X_val, self.y_train, self.y_val = train_test_split(
            self.X, self.y, 
            test_size=0.20, 
            random_state=42,
            stratify=self.y
        )
        
        logger.info(f"Training samples: {len(self.X_train)}")
        logger.info(f"Validation samples: {len(self.X_val)}")

    @staticmethod
    def save_model(path: Path, model: tf.keras.Model):
        model.save(path)
        logger.info(f"Model saved to: {path}")

    def train(self):
        logger.info("Starting training with features...")
        
        # Train using features directly
        self.model.fit(
            self.X_train,
            self.y_train,
            epochs=self.config.params_epochs,
            batch_size=self.config.params_batch_size,
            validation_data=(self.X_val, self.y_val),
            verbose=1
        )

        self.save_model(
            path=self.config.trained_model_path,
            model=self.model
        )

    def copy_model_to_root(self):
        """Copy trained model to root directory for easy access"""
        import shutil
        
        root_model_path = Path("model.h5")
        shutil.copy(self.config.trained_model_path, root_model_path)
        logger.info(f"Model copied to root: {root_model_path}")