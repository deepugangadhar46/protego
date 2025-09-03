"""
AI-powered threat analysis and classification
"""
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio

# ML and NLP imports
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    from textblob import TextBlob
    import numpy as np
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available, using fallback analysis")

# Emergent integrations
try:
    from emergentintegrations import EmergentIntegrations
    EMERGENT_AVAILABLE = True
except ImportError:
    EMERGENT_AVAILABLE = False
    logging.warning("Emergent integrations not available")

logger = logging.getLogger(__name__)

class AIThreatAnalyzer:
    """AI-powered threat analysis and classification"""
    
    def __init__(self):
        self.sentiment_analyzer = None
        self.threat_classifier = None
        self.emergent_client = None
        self.custom_model = None
        self.keyword_patterns = self._load_threat_patterns()
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize AI models"""
        try:
            if TRANSFORMERS_AVAILABLE:
                # Initialize sentiment analysis
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
                )
                
                # Initialize text classification for threats
                self.threat_classifier = pipeline(
                    "text-classification",
                    model="unitary/toxic-bert"
                )
                
                logger.info("AI models initialized successfully")
            
            # Initialize Emergent client if available
            if EMERGENT_AVAILABLE and os.getenv('USE_EMERGENT_LLM', 'false').lower() == 'true':
                self.emergent_client = EmergentIntegrations()
                logger.info("Emergent LLM integration initialized")

            # Load custom scikit-learn model if present
            try:
                from .ml_model import ThreatModel
                model = ThreatModel()
                if model.load():
                    self.custom_model = model
                    logger.info("Custom threat model loaded")
                else:
                    logger.info("Custom threat model not found, continuing without it")
            except Exception as e:
                logger.warning(f"Custom model load failed: {e}")
                
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
            
    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load threat detection patterns"""
        return {
            'physical_threats': [
                'kill', 'murder', 'assassinate', 'bomb', 'attack', 'hurt', 'harm',
                'shoot', 'stab', 'beat', 'punch', 'violence', 'weapon', 'gun', 'knife'
            ],
            'doxxing': [
                'address', 'home', 'phone', 'number', 'location', 'workplace',
                'family', 'children', 'school', 'personal', 'private', 'info'
            ],
            'impersonation': [
                'fake', 'imposter', 'pretend', 'posing', 'identity', 'account',
                'clone', 'duplicate', 'mimicking', 'imitating'
            ],
            'misinformation': [
                'fake news', 'false', 'lie', 'hoax', 'conspiracy', 'rumor',
                'misleading', 'propaganda', 'disinformation', 'fabricated'
            ],
            'harassment': [
                'hate', 'abuse', 'bully', 'troll', 'spam', 'harass',
                'threaten', 'intimidate', 'stalk', 'follow'
            ],
            'reputation_damage': [
                'scandal', 'controversy', 'expose', 'reveal', 'dirt',
                'embarrassing', 'shameful', 'disgrace', 'downfall'
            ]
        }
    
    async def analyze_threat(self, content: str, vip_name: str, platform: str) -> Dict[str, Any]:
        """
        Comprehensive threat analysis using multiple AI approaches
        """
        try:
            # Basic analysis
            basic_analysis = self._basic_threat_analysis(content, vip_name)
            
            # Sentiment analysis
            sentiment_analysis = await self._analyze_sentiment(content)
            
            # AI classification
            ai_classification = await self._classify_with_ai(content, vip_name)
            
            # Advanced LLM analysis (if available)
            llm_analysis = await self._analyze_with_llm(content, vip_name, platform)
            
            # Combine all analyses
            final_analysis = self._combine_analyses(
                basic_analysis, sentiment_analysis, ai_classification, llm_analysis
            )
            
            return final_analysis
            
        except Exception as e:
            logger.error(f"Error in threat analysis: {e}")
            return self._fallback_analysis(content, vip_name)
    
    def _basic_threat_analysis(self, content: str, vip_name: str) -> Dict[str, Any]:
        """Basic keyword-based threat analysis"""
        content_lower = content.lower()
        vip_lower = vip_name.lower()
        
        # Check if VIP is mentioned
        vip_mentioned = vip_lower in content_lower
        
        if not vip_mentioned:
            return {
                'threat_score': 0.0,
                'threat_type': 'none',
                'severity': 'none',
                'indicators': []
            }
        
        # Analyze threat patterns
        threat_indicators = []
        threat_scores = {}
        
        for threat_type, keywords in self.keyword_patterns.items():
            matches = [kw for kw in keywords if kw in content_lower]
            if matches:
                threat_indicators.extend(matches)
                threat_scores[threat_type] = len(matches) / len(keywords)
        
        # Calculate overall threat score
        max_score = max(threat_scores.values(), default=0.0)
        threat_type = max(threat_scores, key=threat_scores.get) if threat_scores else 'harassment'
        
        # Boost score based on context
        context_boosters = {
            'personal_info': ['address', 'phone', 'home', 'family'],
            'urgency': ['now', 'today', 'tonight', 'soon'],
            'capability': ['have', 'will', 'going to', 'plan to']
        }
        
        for booster_type, keywords in context_boosters.items():
            if any(kw in content_lower for kw in keywords):
                max_score += 0.1
        
        return {
            'threat_score': min(max_score, 1.0),
            'threat_type': threat_type,
            'severity': self._calculate_severity(max_score),
            'indicators': threat_indicators[:10]  # Limit indicators
        }

    def _detect_misinfo_impersonation(self, content: str, vip_name: str) -> Dict[str, Any]:
        """Heuristic flags for misinformation and impersonation."""
        text = (content or "").lower()
        vip = (vip_name or "").lower()

        flags: Dict[str, Any] = {
            'is_misinformation': False,
            'is_impersonation': False,
            'misinformation_reasons': [],
            'impersonation_reasons': [],
        }

        # Misinformation cues
        misinfo_keywords = [
            'fake news', 'false claim', 'misinformation', 'disinformation', 'debunked',
            'old photo', 'old video', 'out of context', 'not from', 'edited', 'deepfake'
        ]
        if vip in text and any(k in text for k in misinfo_keywords):
            flags['is_misinformation'] = True
            flags['misinformation_reasons'] = [k for k in misinfo_keywords if k in text][:5]

        # Impersonation cues
        impersonation_keywords = [
            'imposter', 'impersonation', 'fake account', 'not the real', 'posing as', 'pretending to be'
        ]
        if any(k in text for k in impersonation_keywords):
            flags['is_impersonation'] = True
            flags['impersonation_reasons'] = [k for k in impersonation_keywords if k in text][:5]

        return flags
    
    def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """Basic NER using spaCy if available; otherwise empty."""
        try:
            import spacy
            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError:
                return []
            doc = nlp(content or "")
            return [{"text": ent.text, "label": ent.label_} for ent in doc.ents[:20]]
        except Exception:
            return []

    async def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment using AI models"""
        try:
            if self.sentiment_analyzer:
                result = self.sentiment_analyzer(content[:512])  # Limit token length
                sentiment = result[0]['label'].lower()
                confidence = result[0]['score']
                
                # Convert sentiment to threat relevance
                threat_relevance = 0.0
                if sentiment == 'negative':
                    threat_relevance = confidence * 0.5
                elif sentiment == 'neutral':
                    threat_relevance = 0.2
                
                return {
                    'sentiment': sentiment,
                    'confidence': confidence,
                    'threat_relevance': threat_relevance
                }
            else:
                # Fallback to TextBlob
                blob = TextBlob(content)
                polarity = blob.sentiment.polarity
                
                if polarity < -0.3:
                    sentiment = 'negative'
                    threat_relevance = abs(polarity) * 0.5
                elif polarity > 0.3:
                    sentiment = 'positive'
                    threat_relevance = 0.1
                else:
                    sentiment = 'neutral'
                    threat_relevance = 0.2
                
                return {
                    'sentiment': sentiment,
                    'confidence': abs(polarity),
                    'threat_relevance': threat_relevance
                }
                
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {'sentiment': 'unknown', 'confidence': 0.0, 'threat_relevance': 0.3}
    
    async def _classify_with_ai(self, content: str, vip_name: str) -> Dict[str, Any]:
        """Classify content using AI models"""
        try:
            # Prefer custom model if available
            if self.custom_model:
                pred = self.custom_model.predict([content[:1000]])[0]
                return {
                    'toxicity_score': pred.probabilities_by_label.get('toxic', pred.probability),
                    'is_toxic': pred.label.lower() == 'toxic',
                    'model_confidence': pred.probability,
                    'model_label': pred.label,
                    'model_type': 'custom_sklearn'
                }
            if self.threat_classifier:
                result = self.threat_classifier(content[:512])
                toxicity_score = result[0]['score'] if result[0]['label'] == 'TOXIC' else 1 - result[0]['score']
                
                return {
                    'toxicity_score': toxicity_score,
                    'is_toxic': toxicity_score > 0.5,
                    'model_confidence': result[0]['score'],
                    'model_type': 'transformers'
                }
            else:
                return {'toxicity_score': 0.3, 'is_toxic': False, 'model_confidence': 0.0, 'model_type': 'fallback'}
                
        except Exception as e:
            logger.error(f"Error in AI classification: {e}")
            return {'toxicity_score': 0.3, 'is_toxic': False, 'model_confidence': 0.0}
    
    async def _analyze_with_llm(self, content: str, vip_name: str, platform: str) -> Dict[str, Any]:
        """Advanced analysis using LLM"""
        try:
            if not self.emergent_client:
                return {'llm_analysis': None}
            
            prompt = f"""
            Analyze the following content for potential threats against the public figure "{vip_name}" on {platform}:
            
            Content: "{content[:1000]}"
            
            Please provide:
            1. Threat level (0-10 where 10 is most severe)
            2. Threat type (physical, harassment, doxxing, misinformation, impersonation, reputation_damage)
            3. Specific concerns or red flags
            4. Recommended action (monitor, investigate, alert authorities, etc.)
            
            Respond in JSON format with keys: threat_level, threat_type, concerns, recommended_action
            """
            
            response = await self.emergent_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-3.5-turbo",
                temperature=0.1
            )
            
            # Parse LLM response
            llm_result = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            try:
                import json
                llm_data = json.loads(llm_result)
                return {'llm_analysis': llm_data}
            except:
                return {'llm_analysis': {'raw_response': llm_result}}
                
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {'llm_analysis': None}
    
    def _combine_analyses(self, basic: Dict, sentiment: Dict, ai: Dict, llm: Dict) -> Dict[str, Any]:
        """Combine all analysis results into final assessment"""
        
        # Calculate weighted threat score
        scores = []
        weights = []
        
        # Basic analysis (40% weight)
        if basic['threat_score'] > 0:
            scores.append(basic['threat_score'])
            weights.append(0.4)
        
        # Sentiment analysis (20% weight)
        if sentiment['threat_relevance'] > 0:
            scores.append(sentiment['threat_relevance'])
            weights.append(0.2)
        
        # AI toxicity (25% weight)
        if ai['toxicity_score'] > 0:
            scores.append(ai['toxicity_score'])
            weights.append(0.25)
        
        # LLM analysis (15% weight)
        if llm.get('llm_analysis') and isinstance(llm['llm_analysis'], dict):
            llm_score = llm['llm_analysis'].get('threat_level', 0) / 10.0
            if llm_score > 0:
                scores.append(llm_score)
                weights.append(0.15)
        
        # Calculate weighted average
        if scores and weights:
            total_weight = sum(weights)
            weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        else:
            weighted_score = basic['threat_score']
        
        # Determine final threat type
        threat_type = basic['threat_type']
        if llm.get('llm_analysis') and isinstance(llm['llm_analysis'], dict):
            llm_type = llm['llm_analysis'].get('threat_type')
            if llm_type and llm_type in self.keyword_patterns:
                threat_type = llm_type
        
        return {
            'threat_score': min(weighted_score, 1.0),
            'threat_type': threat_type,
            'severity': self._calculate_severity(weighted_score),
            'confidence': self._calculate_confidence(basic, sentiment, ai, llm),
            'analysis_details': {
                'basic_analysis': basic,
                'sentiment_analysis': sentiment,
                'ai_classification': ai,
                'llm_analysis': llm.get('llm_analysis')
            },
            'indicators': basic.get('indicators', []),
            'recommendations': self._generate_recommendations(weighted_score, threat_type)
        }
    
    def _calculate_severity(self, score: float) -> str:
        """Calculate threat severity"""
        if score >= 0.8:
            return 'critical'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        elif score >= 0.2:
            return 'low'
        else:
            return 'minimal'
    
    def _calculate_confidence(self, basic: Dict, sentiment: Dict, ai: Dict, llm: Dict) -> float:
        """Calculate overall confidence in the analysis"""
        confidence_factors = []
        
        # Basic analysis confidence
        if basic['threat_score'] > 0:
            confidence_factors.append(min(len(basic.get('indicators', [])) * 0.1, 0.8))
        
        # Sentiment confidence
        confidence_factors.append(sentiment.get('confidence', 0.5))
        
        # AI model confidence
        confidence_factors.append(ai.get('model_confidence', 0.5))
        
        # LLM confidence (assume high if available)
        if llm.get('llm_analysis'):
            confidence_factors.append(0.8)
        
        return min(sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5, 1.0)
    
    def _generate_recommendations(self, score: float, threat_type: str) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if score >= 0.8:
            recommendations.extend([
                "Immediately alert security team",
                "Consider contacting law enforcement",
                "Preserve all evidence",
                "Monitor for escalation"
            ])
        elif score >= 0.6:
            recommendations.extend([
                "Escalate to security team",
                "Increase monitoring frequency",
                "Document all evidence",
                "Consider platform reporting"
            ])
        elif score >= 0.4:
            recommendations.extend([
                "Continue monitoring",
                "Flag for manual review",
                "Collect additional context"
            ])
        else:
            recommendations.append("Log for trend analysis")
        
        # Threat-specific recommendations
        threat_specific = {
            'physical_threats': ["Contact law enforcement immediately", "Enhance physical security"],
            'doxxing': ["Alert VIP about information exposure", "Consider privacy protection measures"],
            'impersonation': ["Report to platform for identity verification", "Issue public clarification"],
            'misinformation': ["Prepare fact-checking response", "Monitor spread across platforms"],
            'harassment': ["Consider blocking/reporting user", "Document harassment pattern"],
            'reputation_damage': ["Prepare PR response", "Monitor media coverage"]
        }
        
        if threat_type in threat_specific:
            recommendations.extend(threat_specific[threat_type])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _fallback_analysis(self, content: str, vip_name: str) -> Dict[str, Any]:
        """Fallback analysis when AI models fail"""
        basic = self._basic_threat_analysis(content, vip_name)
        return {
            'threat_score': basic['threat_score'],
            'threat_type': basic['threat_type'],
            'severity': basic['severity'],
            'confidence': 0.6,
            'analysis_details': {'basic_analysis': basic},
            'indicators': basic.get('indicators', []),
            'recommendations': ['Manual review recommended due to analysis limitations']
        }

# Global instance
ai_analyzer = AIThreatAnalyzer()

async def analyze_content_for_threats(content: str, vip_name: str, platform: str = 'unknown') -> Dict[str, Any]:
    """
    Main function to analyze content for threats
    """
    return await ai_analyzer.analyze_threat(content, vip_name, platform)