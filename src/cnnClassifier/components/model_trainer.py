# src/cnnClassifier/components/model_trainer.py
import tensorflow as tf
from pathlib import Path
from cnnClassifier import logger
from cnnClassifier.entity.config_entity import TrainingConfig

class Training:
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.train_generator = None
        self.valid_generator = None

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

    def train_valid_generator(self):
        """Create data generators for training and validation"""
        logger.info("Creating data generators...")
        
        datagenerator_kwargs = dict(
            rescale=1./255,
            validation_split=0.20
        )

        dataflow_kwargs = dict(
            target_size=self.config.params_image_size[:-1],
            batch_size=self.config.params_batch_size,
            interpolation="bilinear"
        )

        valid_datagenerator = tf.keras.preprocessing.image.ImageDataGenerator(
            **datagenerator_kwargs
        )

        self.valid_generator = valid_datagenerator.flow_from_directory(
            directory=self.config.training_data,
            subset="validation",
            shuffle=False,
            **dataflow_kwargs
        )

        if self.config.params_is_augmentation:
            logger.info("Using data augmentation...")
            train_datagenerator = tf.keras.preprocessing.image.ImageDataGenerator(
                rotation_range=40,
                horizontal_flip=True,
                width_shift_range=0.2,
                height_shift_range=0.2,
                shear_range=0.2,
                zoom_range=0.2,
                **datagenerator_kwargs
            )
        else:
            train_datagenerator = valid_datagenerator

        self.train_generator = train_datagenerator.flow_from_directory(
            directory=self.config.training_data,
            subset="training",
            shuffle=True,
            **dataflow_kwargs
        )
        
        logger.info(f"Training samples: {self.train_generator.samples}")
        logger.info(f"Validation samples: {self.valid_generator.samples}")
        logger.info(f"Classes: {self.train_generator.class_indices}")

    @staticmethod
    def save_model(path: Path, model: tf.keras.Model):
        model.save(path)
        logger.info(f"Model saved to: {path}")

    def train(self):
        logger.info("Starting training...")
        
        self.steps_per_epoch = (
            self.train_generator.samples // self.train_generator.batch_size
        )
        self.validation_steps = (
            self.valid_generator.samples // self.valid_generator.batch_size
        )
        
        logger.info(f"Steps per epoch: {self.steps_per_epoch}")
        logger.info(f"Validation steps: {self.validation_steps}")

        history = self.model.fit(
            self.train_generator,
            epochs=self.config.params_epochs,
            steps_per_epoch=self.steps_per_epoch,
            validation_steps=self.validation_steps,
            validation_data=self.valid_generator,
            verbose=1
        )

        # Log final metrics
        final_acc = history.history['accuracy'][-1]
        val_acc = history.history['val_accuracy'][-1]
        logger.info(f"Training completed. Final accuracy: {final_acc:.4f}")
        logger.info(f"Validation accuracy: {val_acc:.4f}")

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