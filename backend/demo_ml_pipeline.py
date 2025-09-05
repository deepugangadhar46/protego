#!/usr/bin/env python3
"""
Enhanced ML Pipeline for Fake Content Detection
Implements both TF-IDF baseline and HuggingFace transformers
"""

import os
import pandas as pd
import numpy as np
import joblib
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

# Import fact checker
try:
    from fact_checker import enhanced_fact_check
    FACT_CHECK_AVAILABLE = True
except ImportError:
    FACT_CHECK_AVAILABLE = False
    print("⚠️ Fact checker not available - install requests and python-dotenv")

try:
    from datasets import load_dataset
    from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments, AutoTokenizer, pipeline
    print("✅ All required libraries imported successfully!")
except ImportError as e:
    print(f"❌ Missing required library: {e}")
    print("Please run: pip install datasets transformers scikit-learn kaggle pandas")
    exit(1)

def load_and_preprocess_data():
    """Load and preprocess the dataset"""
    print("📥 Loading dataset...")
    
    # Try to load existing data first
    data_files = ["data/Fake.csv", "data/True.csv"]
    
    if all(os.path.exists(f) for f in data_files):
        print("✅ Using local dataset files")
        # Load local fake news dataset
        fake_df = pd.read_csv("data/Fake.csv")
        true_df = pd.read_csv("data/True.csv")
        
        # Add labels
        fake_df['label'] = 0  # Fake
        true_df['label'] = 1  # True
        
        # Combine datasets
        df = pd.concat([fake_df, true_df], ignore_index=True)
        
        # Use 'text' column or combine title and text
        if 'text' not in df.columns:
            df['text'] = df.get('title', '') + ' ' + df.get('text', '')
        
        df = df[['text', 'label']].dropna()
        
    else:
        print("📥 Downloading dataset from Hugging Face...")
        try:
            dataset = load_dataset("liar")
            train_data = dataset["train"]
            
            df = pd.DataFrame(train_data)
            df = df.rename(columns={"statement": "text"})
            df = df[["text", "label"]].dropna()
            
            # Convert multi-class to binary (fake vs real)
            df['label'] = (df['label'] > 2).astype(int)
            
        except Exception as e:
            print(f"❌ Dataset loading failed: {e}")
            # Create sample data for demo
            return create_sample_data()
    
    print(f"✅ Dataset loaded: {len(df)} samples")
    print(f"   → Label distribution: {df['label'].value_counts().to_dict()}")
    
    return df

def create_sample_data():
    """Create sample fake news data for testing"""
    print("📝 Creating sample dataset...")
    
    fake_news = [
        "BREAKING: Aliens land in Washington DC and meet with president",
        "SHOCKING: Celebrity caught stealing millions from charity",
        "URGENT: Government plans to ban all social media platforms",
        "EXCLUSIVE: Secret documents reveal massive conspiracy",
        "ALERT: New virus spreads through WiFi signals",
        "SCANDAL: Politician admits to being a robot from the future",
        "EXPOSED: Scientists discover earth is actually flat",
        "LEAKED: Government controls weather with secret machines",
        "VIP threatens to destroy economy if demands not met",
        "Celebrity VIP caught in alien abduction scandal"
    ]
    
    real_news = [
        "President announces new infrastructure spending bill",
        "Scientists publish research on climate change effects",
        "Stock market closes higher after economic data release",
        "New healthcare policy aims to reduce prescription costs",
        "University researchers develop improved solar panel technology",
        "Local government approves funding for public transportation",
        "International trade agreement signed between countries",
        "Educational reforms focus on STEM curriculum improvements",
        "VIP announces new charitable foundation launch",
        "Government official provides update on economic policy"
    ]
    
    # Create DataFrame
    data = []
    for text in fake_news:
        data.append({'text': text, 'label': 0})  # 0 = Fake
    for text in real_news:
        data.append({'text': text, 'label': 1})  # 1 = Real
    
    return pd.DataFrame(data)

def train_baseline_model(df):
    """Train TF-IDF + Logistic Regression baseline model"""
    print("\n🔧 Training TF-IDF baseline model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42
    )
    
    # Vectorize
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    
    # Train model
    model = LogisticRegression(max_iter=200, random_state=42)
    model.fit(X_train_tfidf, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"✅ Baseline model trained!")
    print(f"   → Accuracy: {accuracy:.3f}")
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Fake', 'Real']))
    
    # Save model and vectorizer to backend/monitoring/
    monitoring_dir = "backend/monitoring"
    os.makedirs(monitoring_dir, exist_ok=True)
    
    vectorizer_path = os.path.join(monitoring_dir, "tfidf_vectorizer.joblib")
    model_path = os.path.join(monitoring_dir, "threat_model.joblib")
    
    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(model, model_path)
    
    print(f"💾 Vectorizer saved to: {vectorizer_path}")
    print(f"💾 Model saved to: {model_path}")
    
    return model, vectorizer, accuracy

def train_transformer_model(df):
    """Train transformer model for fake news detection"""
    print("\n🚀 Training transformer model...")
    
    try:
        # Use pre-trained HuggingFace model for real-time classification
        classifier = pipeline(
            "text-classification", 
            model="mrm8488/bert-tiny-finetuned-fake-news",
            return_all_scores=True
        )
        
        print("✅ HuggingFace transformer model loaded")
        return classifier
        
    except Exception as e:
        print(f"❌ Transformer loading failed: {e}")
        return None

def test_models(baseline_model, vectorizer, transformer_classifier):
    """Test both models with example texts"""
    print("\n🧪 Testing models with examples...")
    
    examples = [
        "Breaking: VIP X involved in major scandal with evidence",
        "President announces new healthcare policy in official statement",
        "FAKE NEWS: Celebrity seen with aliens in secret meeting",
        "Scientific study confirms climate change effects on agriculture",
        "Unverified: Politician caught in corruption scheme",
        "VIP threatens national security if not given power"
    ]
    
    print("\n📊 Model Comparison Results:")
    print("=" * 60)
    
    for i, text in enumerate(examples, 1):
        print(f"\n{i}. Text: {text}")
        print("-" * 40)
        
        # Baseline model prediction
        if baseline_model and vectorizer:
            text_tfidf = vectorizer.transform([text])
            baseline_pred = baseline_model.predict(text_tfidf)[0]
            baseline_prob = baseline_model.predict_proba(text_tfidf)[0]
            print(f"📈 Baseline: {'REAL' if baseline_pred else 'FAKE'} (confidence: {max(baseline_prob):.3f})")
        
        # Transformer model prediction
        if transformer_classifier:
            try:
                result = transformer_classifier(text)
                if isinstance(result, list) and len(result) > 0:
                    # Get the prediction with highest score
                    best_pred = max(result, key=lambda x: x['score'])
                    print(f"🤖 Transformer: {best_pred['label']} (confidence: {best_pred['score']:.3f})")
            except Exception as e:
                print(f"🤖 Transformer: Error - {e}")
        
        # Fact-check integration
        if FACT_CHECK_AVAILABLE:
            try:
                fact_result = enhanced_fact_check(text)
                credibility = fact_result.get('credibility_analysis', {})
                verdict = credibility.get('verdict', 'unknown')
                score = credibility.get('credibility_score', 0.5)
                print(f"✅ Fact-check: {verdict} (credibility: {score:.3f})")
            except Exception as e:
                print(f"✅ Fact-check: Error - {e}")

def main():
    """Run the complete ML pipeline"""
    print("🚀 Enhanced Fake Content Detection Pipeline")
    print("=" * 50)
    
    # Load and preprocess data
    df = load_and_preprocess_data()
    if df is None:
        return False
    
    # Train baseline model
    baseline_model, vectorizer, baseline_accuracy = train_baseline_model(df)
    
    # Load transformer model
    transformer_classifier = train_transformer_model(df)
    
    # Test both models
    test_models(baseline_model, vectorizer, transformer_classifier)
    
    print("\n🎉 Enhanced ML Pipeline Complete!")
    print("=" * 50)
    print("📁 Models saved to backend/monitoring/:")
    print("   → tfidf_vectorizer.joblib")
    print("   → threat_model.joblib")
    print("\n🔧 Ready for Protego integration!")
    
    if FACT_CHECK_AVAILABLE:
        print("✅ Fact-checking integration enabled")
    else:
        print("⚠️ Fact-checking disabled - set FACT_CHECK_API_KEY in .env")
    
    return True

if __name__ == "__main__":
    print("Starting Enhanced ML Pipeline...")
    print("This will:")
    print("1. Load or create training dataset")
    print("2. Train TF-IDF + Logistic Regression baseline")
    print("3. Load HuggingFace transformer model")
    print("4. Save models to backend/monitoring/")
    print("5. Test both models with examples")
    print()
    
    success = main()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! Models ready for production!")
        print("=" * 50)
        print("📁 Files created:")
        print("   - backend/monitoring/tfidf_vectorizer.joblib")
        print("   - backend/monitoring/threat_model.joblib")
        print("\n💡 Next steps:")
        print("   - Integrate with ai_analyzer.py")
        print("   - Add to service.py pipeline")
        print("   - Set up database logging")
    else:
        print("\n❌ Pipeline failed. Check error messages above.")
