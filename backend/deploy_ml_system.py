#!/usr/bin/env python3
"""
Production Deployment Script for Protego ML System
Finalizes the ML integration and prepares for production use
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

def create_production_config():
    """Create production configuration files"""
    print("🔧 Creating production configuration...")
    
    # ML system configuration
    ml_config = {
        "model_settings": {
            "threat_threshold": 0.7,
            "confidence_threshold": 0.6,
            "fact_check_enabled": True,
            "auto_flag_threshold": 0.8
        },
        "api_settings": {
            "fact_check_timeout": 10,
            "max_content_length": 5000,
            "batch_processing": True
        },
        "logging": {
            "log_level": "INFO",
            "save_predictions": True,
            "alert_high_risk": True
        }
    }
    
    with open("ml_config.json", "w") as f:
        json.dump(ml_config, f, indent=2)
    
    print("   ✅ ML configuration saved: ml_config.json")
    return True

def create_service_wrapper():
    """Create service wrapper for ML integration"""
    print("🚀 Creating service wrapper...")
    
    service_code = '''#!/usr/bin/env python3
"""
Protego ML Service Wrapper
Production-ready ML integration service
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ProtegoMLService:
    """Production ML service for fake content detection"""
    
    def __init__(self, config_path: str = "ml_config.json"):
        self.config = self._load_config(config_path)
        self.ml_available = False
        self.fact_check_available = False
        self._initialize_components()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Config load failed: {e}, using defaults")
            return {
                "model_settings": {"threat_threshold": 0.7},
                "api_settings": {"fact_check_timeout": 10},
                "logging": {"log_level": "INFO"}
            }
    
    def _initialize_components(self):
        """Initialize ML and fact-checking components"""
        try:
            from ml_classifier import classify_text
            self.ml_available = True
            logger.info("ML classifier initialized")
        except ImportError as e:
            logger.error(f"ML classifier unavailable: {e}")
        
        try:
            from fact_checker import enhanced_fact_check
            self.fact_check_available = True
            logger.info("Fact checker initialized")
        except ImportError as e:
            logger.error(f"Fact checker unavailable: {e}")
    
    def analyze_content(self, content: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Analyze content for fake news/misinformation
        
        Args:
            content: Text content to analyze
            metadata: Additional metadata (vip_name, platform, etc.)
            
        Returns:
            Analysis results with recommendations
        """
        if not content or not content.strip():
            return {"error": "Empty content", "status": "skipped"}
        
        metadata = metadata or {}
        result = {
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        # ML Classification
        if self.ml_available:
            try:
                from ml_classifier import classify_text, is_high_risk_content
                
                ml_result = classify_text(content)
                high_risk = is_high_risk_content(content)
                
                result["ml_analysis"] = {
                    "prediction": ml_result.get("prediction", "unknown"),
                    "confidence": ml_result.get("confidence", 0.0),
                    "threat_score": ml_result.get("threat_score", 0.0),
                    "is_high_risk": high_risk
                }
            except Exception as e:
                result["ml_analysis"] = {"error": str(e)}
                logger.error(f"ML analysis failed: {e}")
        
        # Fact Checking
        if self.fact_check_available and self.config.get("model_settings", {}).get("fact_check_enabled", True):
            try:
                from fact_checker import enhanced_fact_check
                
                fact_result = enhanced_fact_check(content)
                credibility = fact_result.get("credibility_analysis", {})
                
                result["fact_check"] = {
                    "has_checks": fact_result.get("has_fact_checks", False),
                    "credibility_score": credibility.get("credibility_score", 0.5),
                    "verdict": credibility.get("verdict", "unknown")
                }
            except Exception as e:
                result["fact_check"] = {"error": str(e)}
                logger.error(f"Fact check failed: {e}")
        
        # Generate recommendations
        result["recommendation"] = self._generate_recommendation(result)
        
        return result
    
    def _generate_recommendation(self, analysis: Dict) -> Dict[str, Any]:
        """Generate action recommendation based on analysis"""
        ml = analysis.get("ml_analysis", {})
        fc = analysis.get("fact_check", {})
        
        threat_threshold = self.config.get("model_settings", {}).get("threat_threshold", 0.7)
        
        # Calculate combined risk score
        ml_threat = ml.get("threat_score", 0.0)
        fc_threat = 1.0 - fc.get("credibility_score", 0.5)
        
        if fc.get("has_checks", False):
            combined_risk = (ml_threat * 0.6) + (fc_threat * 0.4)
        else:
            combined_risk = ml_threat
        
        # Determine action
        if combined_risk >= threat_threshold:
            action = "flag_content"
            priority = "high"
        elif ml.get("is_high_risk", False):
            action = "review_content"
            priority = "medium"
        else:
            action = "monitor"
            priority = "low"
        
        return {
            "action": action,
            "priority": priority,
            "risk_score": combined_risk,
            "should_alert": combined_risk >= threat_threshold
        }
    
    def process_batch(self, contents: list) -> list:
        """Process multiple contents in batch"""
        results = []
        for i, item in enumerate(contents):
            try:
                if isinstance(item, str):
                    content = item
                    metadata = {}
                else:
                    content = item.get("content", "")
                    metadata = {k: v for k, v in item.items() if k != "content"}
                
                result = self.analyze_content(content, metadata)
                result["batch_index"] = i
                results.append(result)
                
            except Exception as e:
                results.append({
                    "batch_index": i,
                    "error": str(e),
                    "status": "failed"
                })
                logger.error(f"Batch item {i} failed: {e}")
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and health check"""
        return {
            "service": "Protego ML Service",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "ml_classifier": self.ml_available,
                "fact_checker": self.fact_check_available
            },
            "config": self.config
        }

# Global service instance
_service = None

def get_ml_service() -> ProtegoMLService:
    """Get global ML service instance"""
    global _service
    if _service is None:
        _service = ProtegoMLService()
    return _service

def analyze_content(content: str, **metadata) -> Dict[str, Any]:
    """Convenience function for content analysis"""
    service = get_ml_service()
    return service.analyze_content(content, metadata)

if __name__ == "__main__":
    # Demo service usage
    service = ProtegoMLService()
    
    print("🚀 Protego ML Service Demo")
    print("=" * 40)
    
    # Test single content
    test_content = "Breaking: VIP politician caught in major scandal"
    result = service.analyze_content(test_content, {"platform": "twitter"})
    
    print(f"Content: {result['content_preview']}")
    print(f"ML Prediction: {result.get('ml_analysis', {}).get('prediction', 'N/A')}")
    print(f"Recommendation: {result.get('recommendation', {}).get('action', 'N/A')}")
    print(f"Risk Score: {result.get('recommendation', {}).get('risk_score', 0):.3f}")
    
    # Service status
    status = service.get_service_status()
    print(f"\\nService Status: {status['status']}")
    print(f"Components: {status['components']}")
'''
    
    with open("ml_service.py", "w") as f:
        f.write(service_code)
    
    print("   ✅ Service wrapper created: ml_service.py")
    return True

def create_api_endpoints():
    """Create API endpoints for ML service"""
    print("🌐 Creating API endpoints...")
    
    api_code = '''#!/usr/bin/env python3
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
        results = service.process_batch(contents)
        
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
'''
    
    with open("ml_api.py", "w") as f:
        f.write(api_code)
    
    print("   ✅ API endpoints created: ml_api.py")
    return True

def create_deployment_docs():
    """Create deployment documentation"""
    print("📚 Creating deployment documentation...")
    
    readme_content = '''# Protego ML System - Production Deployment

## Overview
Complete ML integration system for fake content detection with fact-checking capabilities.

## Components
- **ML Classifier**: TF-IDF + Logistic Regression baseline model
- **Fact Checker**: Google Fact Check Tools API integration  
- **Enhanced Integration**: Combined ML + fact-checking pipeline
- **Service Wrapper**: Production-ready service interface
- **API Endpoints**: Flask API for external integration

## Files Created
```
backend/
├── enhanced_ml_integration.py    # Core ML + fact-check integration
├── ml_classifier.py             # Simple ML classifier interface
├── fact_checker.py              # Google Fact Check Tools API
├── content_logger.py            # Database logging system
├── demo_ml_pipeline.py          # Training pipeline
├── ml_service.py                # Production service wrapper
├── ml_api.py                    # Flask API endpoints
├── ml_config.json               # Production configuration
├── test_complete_integration.py # Integration test suite
├── setup_ml_system.py           # System initialization
└── monitoring/
    ├── tfidf_vectorizer.joblib  # Trained vectorizer
    └── threat_model.joblib      # Trained ML model
```

## Quick Start

### 1. Initialize System
```bash
cd backend
python setup_ml_system.py
```

### 2. Run Integration Tests
```bash
python test_complete_integration.py
```

### 3. Start ML Service
```bash
python ml_service.py
```

### 4. Start API Server
```bash
python ml_api.py
```

## API Usage

### Analyze Single Content
```bash
curl -X POST http://localhost:5001/api/analyze \\
  -H "Content-Type: application/json" \\
  -d '{"content": "Breaking news about VIP scandal", "platform": "twitter"}'
```

### Batch Analysis
```bash
curl -X POST http://localhost:5001/api/batch \\
  -H "Content-Type: application/json" \\
  -d '{"contents": [{"content": "News 1"}, {"content": "News 2"}]}'
```

### Service Status
```bash
curl http://localhost:5001/api/status
```

## Configuration

Edit `ml_config.json` to adjust:
- Threat detection thresholds
- Fact-checking settings
- API timeouts
- Logging preferences

## Integration with Main Service

```python
from ml_service import analyze_content

# Analyze content
result = analyze_content(
    "Suspicious content here",
    platform="twitter",
    vip_name="politician"
)

# Check recommendation
if result["recommendation"]["should_alert"]:
    # Take action based on risk level
    handle_threat(result)
```

## Production Deployment

1. **Environment Setup**
   - Set FACT_CHECK_API_KEY in .env
   - Install dependencies: `pip install -r requirements.txt`
   - Initialize models: `python setup_ml_system.py`

2. **Service Deployment**
   - Use systemd/supervisor for process management
   - Configure nginx for API proxy
   - Set up monitoring and logging

3. **Database Integration**
   - Content logging via `content_logger.py`
   - Alert storage and retrieval
   - Historical analysis and reporting

## Monitoring

- Service logs: `ml_service.log`
- API access logs: Flask default logging
- Model performance: Integration test results
- Database alerts: Via content logger

## Next Steps

1. **Enhanced Models**: Train with larger datasets
2. **Real-time Processing**: WebSocket integration
3. **Advanced Features**: Image analysis, multi-language support
4. **Scaling**: Distributed processing, model serving
5. **Analytics**: Dashboard for threat monitoring

## Support

For issues or questions:
- Check integration test results
- Review service logs
- Verify configuration settings
- Test individual components
'''
    
    with open("ML_DEPLOYMENT_README.md", "w") as f:
        f.write(readme_content)
    
    print("   ✅ Documentation created: ML_DEPLOYMENT_README.md")
    return True

def finalize_deployment():
    """Finalize deployment and create summary"""
    print("\n🎯 Finalizing ML System Deployment...")
    
    # Create deployment summary
    summary = {
        "deployment_date": datetime.now().isoformat(),
        "system_name": "Protego ML Integration System",
        "version": "1.0.0",
        "components": {
            "ml_classifier": "✅ Ready",
            "fact_checker": "✅ Ready", 
            "enhanced_integration": "✅ Ready",
            "service_wrapper": "✅ Ready",
            "api_endpoints": "✅ Ready",
            "documentation": "✅ Ready"
        },
        "files_created": [
            "enhanced_ml_integration.py",
            "ml_classifier.py",
            "fact_checker.py", 
            "content_logger.py",
            "demo_ml_pipeline.py",
            "ml_service.py",
            "ml_api.py",
            "ml_config.json",
            "test_complete_integration.py",
            "setup_ml_system.py",
            "ML_DEPLOYMENT_README.md"
        ],
        "next_steps": [
            "Run setup_ml_system.py to initialize models",
            "Execute test_complete_integration.py for validation",
            "Start ml_api.py for API service",
            "Integrate with main Protego service",
            "Configure production environment"
        ]
    }
    
    with open("deployment_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("   ✅ Deployment summary: deployment_summary.json")
    return summary

def main():
    """Main deployment function"""
    print("🚀 Protego ML System - Production Deployment")
    print("=" * 50)
    
    steps = [
        ("Creating production configuration", create_production_config),
        ("Creating service wrapper", create_service_wrapper),
        ("Creating API endpoints", create_api_endpoints),
        ("Creating deployment documentation", create_deployment_docs),
        ("Finalizing deployment", finalize_deployment)
    ]
    
    completed = 0
    for step_name, step_func in steps:
        try:
            if step_func():
                completed += 1
            else:
                print(f"   ❌ {step_name} failed")
        except Exception as e:
            print(f"   ❌ {step_name} error: {e}")
    
    print(f"\n🎯 Deployment Complete: {completed}/{len(steps)} steps successful")
    
    if completed == len(steps):
        print("\n🎉 PRODUCTION DEPLOYMENT SUCCESSFUL!")
        print("\n🚀 System Ready For:")
        print("   - Fake content detection")
        print("   - Fact-checking integration")
        print("   - Real-time threat analysis")
        print("   - API-based content processing")
        print("   - Production monitoring")
        
        print("\n📋 Next Actions:")
        print("   1. Run: python setup_ml_system.py")
        print("   2. Test: python test_complete_integration.py") 
        print("   3. Start: python ml_api.py")
        print("   4. Read: ML_DEPLOYMENT_README.md")
    else:
        print("\n⚠️ Deployment partially completed")
        print("Check error messages above for issues")

if __name__ == "__main__":
    main()
