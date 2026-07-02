# src/cnnClassifier/pipeline/stage_05_model_trainer.py
from cnnClassifier.config.configuration import ConfigurationManager
from cnnClassifier.components.model_trainer import Training
from cnnClassifier import logger

STAGE_NAME = "Training"

class ModelTrainingPipeline:
    def __init__(self):
        pass

    def main(self):
        config = ConfigurationManager()
        training_config = config.get_training_config()
        training = Training(config=training_config)
        
        # Step 1: Load base model
        training.get_base_model()
        
        # Step 2: Prepare data generators (using raw images)
        training.train_valid_generator()
        
        # Step 3: Train the model
        training.train()
        
        # Step 4: Copy model to root folder
        training.copy_model_to_root()

if __name__ == '__main__': 
    try:
        logger.info(f"*******************")
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        obj = ModelTrainingPipeline()
        obj.main()
        logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
    except Exception as e:
        logger.exception(e)
        raise e