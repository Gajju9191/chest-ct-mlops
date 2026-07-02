# src/cnnClassifier/entity/config_entity.py

from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    source_URL: str
    local_data_file: Path
    unzip_dir: Path

@dataclass(frozen=True)
class PrepareBaseModelConfig:
    root_dir: Path
    base_model_path: Path
    updated_base_model_path: Path
    params_image_size: list
    params_learning_rate: float
    params_include_top: bool
    params_weights: str
    params_classes: int

# ✅ NEW: Feature Engineering Config
@dataclass(frozen=True)
class FeatureEngineeringConfig:
    root_dir: Path
    features_file: Path
    metadata_file: Path
    scaler_file: Path
    pca_file: Path
    training_data: Path
    use_pca: bool
    pca_components: int
    use_deep_features: bool
    use_radiomic_features: bool

# ✅ NEW: Training Drift Config
@dataclass(frozen=True)
class TrainingDriftConfig:
    root_dir: Path
    report_file: Path
    metrics_file: Path
    features_file: Path
    threshold: float
    test_type: str

@dataclass(frozen=True)
class TrainingConfig:
    root_dir: Path
    trained_model_path: Path
    updated_base_model_path: Path
    training_data: Path
    params_epochs: int
    params_batch_size: int
    params_is_augmentation: bool
    params_image_size: list
    params_learning_rate: float

@dataclass(frozen=True)
class EvaluationConfig:
    root_dir: Path
    model_path: Path
    training_data: Path
    metrics_file: Path
    confusion_matrix_path: Path
    mlflow_uri: str
    params_batch_size: int
    params_image_size: list
    params_classes: int