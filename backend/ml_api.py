#!/usr/bin/env python3
"""
Protego ML API Endpoints
Flask API for ML service integration
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_service import get_ml_service

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze_content():
    """Analyze single content for fake news/misinformation"""
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({"error": "Missing content field"}), 400
        
        content = data['content']
        metadata = {k: v for k, v in data.items() if k != 'content'}
        
        service = get_ml_service()
        result = service.analyze_content(content, metadata)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def analyze_batch():
    """Analyze multiple contents in batch"""
    try:
        data = request.get_json()
        
        if not data or 'contents' not in data:
            return jsonify({"error": "Missing contents field"}), 400
        
        contents = data['contents']
        if not isinstance(contents, list):
            return jsonify({"error": "Contents must be a list"}), 400
        
        service = get_ml_service()
        results = []
        
        for i, item in enumerate(contents):
            try:
                if isinstance(item, str):
                    content = item
                    metadata = {}
                else:
                    content = item.get("content", "")
                    metadata = {k: v for k, v in item.items() if k != "content"}
                
                result = service.analyze_content(content, metadata)
                result["batch_index"] = i
                results.append(result)
                
            except Exception as e:
                results.append({
                    "batch_index": i,
                    "error": str(e),
                    "status": "failed"
                })
        
        return jsonify({"results": results, "total": len(results)})
        
    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def service_status():
    """Get service status and health check"""
    try:
        service = get_ml_service()
        status = service.get_service_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "service": "Protego ML API"})

if __name__ == '__main__':
    print("🚀 Starting Protego ML API...")
    print("Endpoints available:")
    print("  POST /api/analyze - Analyze single content")
    print("  POST /api/batch - Analyze multiple contents")
    print("  GET /api/status - Service status")
    print("  GET /api/health - Health check")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=False)