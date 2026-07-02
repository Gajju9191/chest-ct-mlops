# src/cnnClassifier/config/configuration.py
from pathlib import Path
from cnnClassifier.constants import CONFIG_FILE_PATH, PARAMS_FILE_PATH
from cnnClassifier.utils.common import read_yaml, create_directories
from cnnClassifier.entity.config_entity import (
    DataIngestionConfig,
    PrepareBaseModelConfig,
    TrainingConfig,
    EvaluationConfig,
    FeatureEngineeringConfig,  # ✅ NEW
    TrainingDriftConfig       # ✅ NEW
)

class ConfigurationManager:
    def __init__(self, config_filepath=CONFIG_FILE_PATH, params_filepath=PARAMS_FILE_PATH):
        self.config = read_yaml(config_filepath)
        self.params = read_yaml(params_filepath)
        create_directories([self.config.artifacts_root])
    
    def get_data_ingestion_config(self) -> DataIngestionConfig:
        config = self.config.data_ingestion
        create_directories([config.root_dir])
        
        return DataIngestionConfig(
            root_dir=Path(config.root_dir),
            source_URL=config.source_URL,
            local_data_file=Path(config.local_data_file),
            unzip_dir=Path(config.unzip_dir)
        )
    
    def get_prepare_base_model_config(self) -> PrepareBaseModelConfig:
        config = self.config.prepare_base_model
        create_directories([config.root_dir])
        
        return PrepareBaseModelConfig(
            root_dir=Path(config.root_dir),
            base_model_path=Path(config.base_model_path),
            updated_base_model_path=Path(config.updated_base_model_path),
            params_image_size=self.params.IMAGE_SIZE,
            params_learning_rate=self.params.LEARNING_RATE,
            params_include_top=self.params.INCLUDE_TOP,
            params_weights=self.params.WEIGHTS,
            params_classes=self.params.CLASSES
        )
    
    # ✅ NEW: Feature Engineering Config
    def get_feature_engineering_config(self) -> FeatureEngineeringConfig:
        config = self.config.feature_engineering
        create_directories([config.root_dir])
        
        # Get training data path
        training_data = Path(self.config.data_ingestion.unzip_dir) / "Chest-CT-Scan-data"
        
        # Get feature engineering params
        feature_params = self.params.FEATURE_ENGINEERING
        
        return FeatureEngineeringConfig(
            root_dir=Path(config.root_dir),
            features_file=Path(config.features_file),
            metadata_file=Path(config.metadata_file),
            scaler_file=Path(config.scaler_file),
            pca_file=Path(config.pca_file),
            training_data=training_data,
            use_pca=feature_params.use_pca,
            pca_components=feature_params.pca_components,
            use_deep_features=feature_params.use_deep_features,
            use_radiomic_features=feature_params.use_radiomic_features
        )
    
    # ✅ NEW: Training Drift Config
    def get_training_drift_config(self) -> TrainingDriftConfig:
        config = self.config.training_drift
        create_directories([config.root_dir])
        
        # Get drift params
        drift_params = self.params.DRIFT_DETECTION
        
        return TrainingDriftConfig(
            root_dir=Path(config.root_dir),
            report_file=Path(config.report_file),
            metrics_file=Path(config.metrics_file),
            features_file=Path(self.config.feature_engineering.features_file),
            threshold=drift_params.threshold,
            test_type=drift_params.test_type
        )
    
    def get_training_config(self) -> TrainingConfig:
        training = self.config.training
        prepare_base_model = self.config.prepare_base_model
        
        # ✅ UPDATED: Use features directory for training
        training_data = Path(self.config.feature_engineering.root_dir)
        create_directories([Path(training.root_dir)])
        
        return TrainingConfig(
            root_dir=Path(training.root_dir),
            trained_model_path=Path(training.trained_model_path),
            updated_base_model_path=Path(prepare_base_model.updated_base_model_path),
            training_data=training_data,  # Now points to features
            params_epochs=self.params.EPOCHS,
            params_batch_size=self.params.BATCH_SIZE,
            params_is_augmentation=self.params.AUGMENTATION,
            params_image_size=self.params.IMAGE_SIZE,
            params_learning_rate=self.params.LEARNING_RATE
        )
    
    def get_evaluation_config(self) -> EvaluationConfig:
        eval_cfg = self.config.evaluation
        training_data = Path(self.config.data_ingestion.unzip_dir) / "Chest-CT-Scan-data"
        create_directories([eval_cfg.root_dir])
        
        return EvaluationConfig(
            root_dir=Path(eval_cfg.root_dir),
            model_path=Path(self.config.training.trained_model_path),
            training_data=training_data,
            metrics_file=Path(eval_cfg.metrics_file),
            confusion_matrix_path=Path(eval_cfg.confusion_matrix_path),
            mlflow_uri=self.config.mlflow_uri,
            params_batch_size=self.params.BATCH_SIZE,
            params_image_size=self.params.IMAGE_SIZE,
            params_classes=self.params.CLASSES
        )