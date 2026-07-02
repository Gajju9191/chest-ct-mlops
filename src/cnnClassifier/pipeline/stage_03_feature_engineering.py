
"""
Feature Engineering Pipeline Stage
"""
from cnnClassifier.config.configuration import ConfigurationManager
from cnnClassifier.components.feature_engineering import FeatureEngineering
from cnnClassifier import logger

STAGE_NAME = "Feature Engineering Stage"

class FeatureEngineeringPipeline:
    def __init__(self):
        pass
    
    def main(self):
        try:
            logger.info(f" Starting {STAGE_NAME}")
            
            config = ConfigurationManager()
            
            # Get feature engineering config
            feature_config = config.get_feature_engineering_config()
            
            # Run feature engineering
            feature_engineering = FeatureEngineering(feature_config)
            feature_engineering.run()
            
            logger.info(f"✅ {STAGE_NAME} completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ {STAGE_NAME} failed: {e}")
            raise e

if __name__ == '__main__':
    try:
        logger.info(f">>>>>>> stage {STAGE_NAME} started <<<<<<<")
        obj = FeatureEngineeringPipeline()
        obj.main()
        logger.info(f">>>>>>> stage {STAGE_NAME} completed <<<<<<<\n\n==========x==========")
    except Exception as e:
        logger.exception(e)
        raise e