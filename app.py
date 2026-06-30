# app.py
from flask import Flask, request, jsonify, render_template
import os
import sys
from flask_cors import CORS, cross_origin
from pathlib import Path
import boto3
import tensorflow as tf
import logging

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from cnnClassifier.utils.common import decodeImage
from cnnClassifier.pipeline.prediction import PredictionPipeline
from cnnClassifier.utils.secrets_manager import SecretsManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.putenv('LANG', 'en_US.UTF-8')
os.putenv('LC_ALL', 'en_US.UTF-8')

app = Flask(__name__)
CORS(app)

# Initialize Secrets Manager
secrets = SecretsManager()

# Get model bucket from secrets
MODEL_BUCKET = secrets.get_s3_credentials().get('models_bucket', 'chest-ct-models-155407238004')
MODEL_KEY = os.environ.get('MODEL_KEY', 'model.h5')
LOCAL_MODEL_PATH = '/tmp/model.h5'


def download_model_from_s3():
    """Download model from S3 bucket"""
    try:
        s3 = boto3.client('s3')
        s3.download_file(MODEL_BUCKET, MODEL_KEY, LOCAL_MODEL_PATH)
        logger.info(f"✅ Model downloaded from s3://{MODEL_BUCKET}/{MODEL_KEY}")
        return tf.keras.models.load_model(LOCAL_MODEL_PATH)
    except Exception as e:
        logger.error(f"❌ Failed to download model from S3: {e}")
        return None


class ClientApp:
    def __init__(self):
        self.filename = "inputImage.jpg"
        self.classifier = PredictionPipeline(self.filename)
        self.model = None
    
    def load_model(self):
        """Load model from S3 or local"""
        # Try to download from S3 first
        self.model = download_model_from_s3()
        
        if self.model is not None:
            self.classifier.model = self.model
            logger.info("✅ Model loaded from S3")
            return True
        else:
            logger.warning("⚠️ Trying to load local model...")
            try:
                self.classifier.load_model()
                self.model = self.classifier.model
                logger.info("✅ Model loaded locally")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to load model locally: {e}")
                return False


@app.route("/", methods=['GET'])
@cross_origin()
def home():
    return render_template('index.html')


@app.route("/train", methods=['GET', 'POST'])
@cross_origin()
def trainRoute():
    try:
        os.system("dvc repro")
        clApp.load_model()
        return "Training done successfully! Model reloaded."
    except Exception as e:
        return f"Training failed: {str(e)}", 500


@app.route("/predict", methods=['POST'])
@cross_origin()
def predictRoute():
    try:
        if request.is_json:
            image = request.json['image']
            decodeImage(image, clApp.filename)
        else:
            file = request.files['image']
            file.save(clApp.filename)
        
        result = clApp.classifier.predict()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict_batch", methods=['POST'])
@cross_origin()
def predictBatchRoute():
    try:
        if 'images' not in request.files:
            return jsonify({"error": "No images provided"}), 400
        
        files = request.files.getlist('images')
        
        if len(files) == 0:
            return jsonify({"error": "No files selected"}), 400
        
        results = []
        
        for file in files:
            if file.filename == '':
                continue
                
            file.save(clApp.filename)
            result = clApp.classifier.predict()
            result["filename"] = file.filename
            results.append(result)
        
        if os.path.exists(clApp.filename):
            os.remove(clApp.filename)
        
        return jsonify({
            "total": len(results),
            "results": results
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=['GET'])
@cross_origin()
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": clApp.model is not None,
        "model_bucket": MODEL_BUCKET
    })


# Create global instance
clApp = ClientApp()

if __name__ == "__main__":
    model_loaded = clApp.load_model()
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask app on port {port}")
    logger.info(f"Model loaded: {model_loaded}")
    app.run(host='0.0.0.0', port=port, debug=False)