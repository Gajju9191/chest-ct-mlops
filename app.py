# app.py
from flask import Flask, request, jsonify, render_template
import os
import sys
from flask_cors import CORS, cross_origin
from pathlib import Path
import boto3
import tensorflow as tf

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from cnnClassifier.utils.common import decodeImage
from cnnClassifier.pipeline.prediction import PredictionPipeline

os.putenv('LANG', 'en_US.UTF-8')
os.putenv('LC_ALL', 'en_US.UTF-8')

app = Flask(__name__)
CORS(app)

# S3 Configuration
MODEL_BUCKET = os.environ.get('MODEL_BUCKET', 'chest-ct-models-155407238004')
MODEL_KEY = os.environ.get('MODEL_KEY', 'model.h5')
LOCAL_MODEL_PATH = '/tmp/model.h5'


def download_model_from_s3():
    """Download model from S3 bucket"""
    try:
        s3 = boto3.client('s3')
        s3.download_file(MODEL_BUCKET, MODEL_KEY, LOCAL_MODEL_PATH)
        print(f"✅ Model downloaded from s3://{MODEL_BUCKET}/{MODEL_KEY}")
        return tf.keras.models.load_model(LOCAL_MODEL_PATH)
    except Exception as e:
        print(f"❌ Failed to download model from S3: {e}")
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
            # Set model in classifier
            self.classifier.model = self.model
            print("✅ Model loaded from S3")
        else:
            # Fallback to local model loading
            print("⚠️ Trying to load local model...")
            self.classifier.load_model()
            self.model = self.classifier.model
            print("✅ Model loaded locally")


@app.route("/", methods=['GET'])
@cross_origin()
def home():
    return render_template('index.html')


@app.route("/train", methods=['GET', 'POST'])
@cross_origin()
def trainRoute():
    try:
        # Run DVC pipeline to retrain model
        os.system("dvc repro")
        # Reload model after training
        clApp.load_model()
        return "Training done successfully! Model reloaded."
    except Exception as e:
        return f"Training failed: {str(e)}", 500


@app.route("/predict", methods=['POST'])
@cross_origin()
def predictRoute():
    try:
        # Get image from request (supports both JSON and form-data)
        if request.is_json:
            image = request.json['image']
            decodeImage(image, clApp.filename)
        else:
            # Handle file upload
            file = request.files['image']
            file.save(clApp.filename)
        
        # Make prediction
        result = clApp.classifier.predict()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict_batch", methods=['POST'])
@cross_origin()
def predictBatchRoute():
    try:
        # Check if multiple files are uploaded
        if 'images' not in request.files:
            return jsonify({"error": "No images provided"}), 400
        
        files = request.files.getlist('images')
        
        if len(files) == 0:
            return jsonify({"error": "No files selected"}), 400
        
        results = []
        
        for file in files:
            if file.filename == '':
                continue
                
            # Save file temporarily
            file.save(clApp.filename)
            
            # Make prediction
            result = clApp.classifier.predict()
            
            # Add filename to result
            result["filename"] = file.filename
            
            results.append(result)
        
        # Clean up
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


if __name__ == "__main__":
    clApp = ClientApp()
    # Load model on startup (will download from S3)
    clApp.load_model()
    print(f"Model loaded: {clApp.model is not None}")
    app.run(host='0.0.0.0', port=8080, debug=False)