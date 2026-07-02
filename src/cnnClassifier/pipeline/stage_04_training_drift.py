# src/cnnClassifier/pipeline/stage_04_training_drift.py
from pathlib import Path
from cnnClassifier.config.configuration import ConfigurationManager
from cnnClassifier.components.training_drift import TrainingDriftDetector
from cnnClassifier import logger

STAGE_NAME = "Training Drift Detection Stage"

class TrainingDriftPipeline:
    def __init__(self):
        pass
    
    def main(self):
        try:
            logger.info(f"Starting {STAGE_NAME}")
            
            config = ConfigurationManager()
            
            # Get config
            drift_config = config.get_training_drift_config()
            
            # Initialize detector
            detector = TrainingDriftDetector(drift_config)
            
            # Load reference data if exists
            reference_path = Path("artifacts/reference/reference_features.csv")
            if reference_path.exists():
                detector.load_reference_data(reference_path)
            
            # Detect drift
            new_data_path = Path(drift_config.features_file)
            report = detector.detect_drift(new_data_path)
            
            # Save report
            output_path = Path(drift_config.report_file)
            detector.save_report(report, output_path)
            
            # Save reference for next time
            reference_path.parent.mkdir(parents=True, exist_ok=True)
            if detector.reference_data is not None:
                detector.reference_data.to_csv(reference_path, index=False)
            
            logger.info(f"{STAGE_NAME} completed successfully!")
            logger.info(f"Drift: {report['drift_percentage']:.1f}% - {report['recommendation']}")
            
        except Exception as e:
            logger.error(f"{STAGE_NAME} failed: {e}")
            raise e

if __name__ == '__main__':
    try:
        logger.info(f">>>>>>> stage {STAGE_NAME} started <<<<<<<")
        obj = TrainingDriftPipeline()
        obj.main()
        logger.info(f">>>>>>> stage {STAGE_NAME} completed <<<<<<<\n\n==========x==========")
    except Exception as e:
        logger.exception(e)
        raise e