import google.generativeai as genai
from PIL import Image
import io
import json
import os
import joblib
import bcrypt
import jwt
import base64
import numpy as np
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# After this line:
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Add this:
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API configured successfully")
else:
    print("⚠️ Warning: GEMINI_API_KEY not found")

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
JWT_SECRET = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Initialize Supabase
try:
    from supabase import create_client, Client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    SUPABASE_CONNECTED = True
    print("✅ Supabase connected successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not connect to Supabase - {e}")
    supabase = None
    SUPABASE_CONNECTED = False

# Load ML models
try:
    risk_classifier = joblib.load('models/risk_classifier.pkl')
    risk_encoder = joblib.load('models/risk_encoder.pkl')
    risk_scaler = joblib.load('models/risk_scaler.pkl')
    MODELS_LOADED = True
    print("✅ ML Models loaded successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not load models - {e}")
    risk_classifier = None
    risk_encoder = None
    risk_scaler = None
    MODELS_LOADED = False

# Knowledge Base
INGREDIENT_DATA = {
    'water': {'risk': 0, 'beneficial': True, 'category': 'solvent'},
    'aqua': {'risk': 0, 'beneficial': True, 'category': 'solvent'},
    'glycerin': {'risk': 5, 'beneficial': True, 'category': 'humectant'},
    'niacinamide': {'risk': 10, 'beneficial': True, 'category': 'vitamin'},
    'hyaluronic acid': {'risk': 5, 'beneficial': True, 'category': 'humectant'},
    'sodium hyaluronate': {'risk': 5, 'beneficial': True, 'category': 'humectant'},
    'retinol': {'risk': 40, 'beneficial': True, 'category': 'anti-aging'},
    'fragrance': {'risk': 60, 'beneficial': False, 'category': 'fragrance'},
    'parfum': {'risk': 60, 'beneficial': False, 'category': 'fragrance'},
    'alcohol': {'risk': 50, 'beneficial': False, 'category': 'solvent'},
    'alcohol denat': {'risk': 50, 'beneficial': False, 'category': 'solvent'},
    'parabens': {'risk': 70, 'beneficial': False, 'category': 'preservative'},
    'methylparaben': {'risk': 70, 'beneficial': False, 'category': 'preservative'},
    'propylparaben': {'risk': 70, 'beneficial': False, 'category': 'preservative'},
    'sulfates': {'risk': 65, 'beneficial': False, 'category': 'surfactant'},
    'sls': {'risk': 65, 'beneficial': False, 'category': 'surfactant'},
    'sodium lauryl sulfate': {'risk': 65, 'beneficial': False, 'category': 'surfactant'},
    'salicylic acid': {'risk': 30, 'beneficial': True, 'category': 'exfoliant'},
    'vitamin c': {'risk': 15, 'beneficial': True, 'category': 'antioxidant'},
    'ascorbic acid': {'risk': 15, 'beneficial': True, 'category': 'antioxidant'},
    'cetearyl alcohol': {'risk': 10, 'beneficial': True, 'category': 'emollient'},
    'cetyl alcohol': {'risk': 10, 'beneficial': True, 'category': 'emollient'},
    'shea butter': {'risk': 5, 'beneficial': True, 'category': 'emollient'},
    'coconut oil': {'risk': 35, 'beneficial': True, 'category': 'oil'},
    'jojoba oil': {'risk': 10, 'beneficial': True, 'category': 'oil'},
}

HARMFUL_INGREDIENTS = {
    'high_risk': ['parabens', 'methylparaben', 'propylparaben', 'butylparaben',
                  'formaldehyde', 'toluene', 'phthalates', 'triclosan'],
    'moderate_risk': ['sulfates', 'sls', 'sodium lauryl sulfate', 'fragrance', 
                      'parfum', 'alcohol denat'],
    'comedogenic': ['coconut oil', 'cocoa butter', 'isopropyl myristate'],
    'irritants': ['menthol', 'camphor', 'eucalyptus']
}

SKIN_TYPE_CONCERNS = {
    'sensitive': ['fragrance', 'parfum', 'alcohol', 'sulfates', 'retinol', 'alcohol denat'],
    'dry': ['alcohol', 'sulfates', 'alcohol denat', 'sls'],
    'oily': ['coconut oil', 'palm oil', 'mineral oil'],
    'acne': ['coconut oil', 'palm oil', 'isopropyl myristate']
}

# Product Database (Simulated)
PRODUCT_DATABASE = {
    'cerave moisturizing cream': {
        'name': 'CeraVe Moisturizing Cream',
        'ingredients': 'water, glycerin, cetearyl alcohol, caprylic triglyceride, cetyl alcohol, ceramide np, ceramide ap, ceramide eop, carbomer, dimethicone, hyaluronic acid, cholesterol, sodium lauroyl lactylate, xanthan gum',
        'category': 'moisturizer',
        'brand': 'CeraVe',
        'concerns': ['dry skin', 'eczema', 'sensitive skin'],
        'suitable_skin_types': ['dry', 'normal', 'sensitive']
    },
    'cerave hydrating cleanser': {
        'name': 'CeraVe Hydrating Facial Cleanser',
        'ingredients': 'water, glycerin, cetearyl alcohol, phenoxyethanol, stearyl alcohol, cetyl alcohol, ceramide np, ceramide ap, ceramide eop, carbomer, hyaluronic acid, cholesterol, sodium lauroyl lactylate, xanthan gum',
        'category': 'cleanser',
        'brand': 'CeraVe',
        'concerns': ['dry skin', 'normal skin'],
        'suitable_skin_types': ['dry', 'normal', 'sensitive']
    },
    'neutrogena hydro boost': {
        'name': 'Neutrogena Hydro Boost Water Gel',
        'ingredients': 'water, dimethicone, glycerin, dimethicone crosspolymer, phenoxyethanol, dimethicone peg-10 phosphate, synthetic beeswax, trehalose, sodium hyaluronate, ethylhexylglycerin, cetearyl olivate, sorbitan olivate, dimethiconol, sodium polyacrylate',
        'category': 'moisturizer',
        'brand': 'Neutrogena',
        'concerns': ['hydration', 'dry skin'],
        'suitable_skin_types': ['all']
    },
    'la roche-posay toleriane': {
        'name': 'La Roche-Posay Toleriane Double Repair Moisturizer',
        'ingredients': 'water, glycerin, dimethicone, niacinamide, cetearyl alcohol, phenoxyethanol, ceramide np, ceramide ap, ceramide eop, sodium hyaluronate',
        'category': 'moisturizer',
        'brand': 'La Roche-Posay',
        'concerns': ['sensitive skin', 'redness'],
        'suitable_skin_types': ['sensitive', 'normal', 'dry']
    },
    'the ordinary niacinamide': {
        'name': 'The Ordinary Niacinamide 10% + Zinc 1%',
        'ingredients': 'water, niacinamide, pentylene glycol, zinc pca, dimethyl isosorbide, tamarindus indica seed gum, xanthan gum, isoceteth-20, ethoxydiglycol, phenoxyethanol, chlorphenesin',
        'category': 'serum',
        'brand': 'The Ordinary',
        'concerns': ['acne', 'pores', 'oil control'],
        'suitable_skin_types': ['oily', 'acne', 'combination']
    }
}

# Allergy Analysis Knowledge Base
ALLERGY_SYMPTOMS = {
    'redness': ['fragrance', 'alcohol', 'essential oils', 'sulfates'],
    'itching': ['fragrance', 'parabens', 'formaldehyde', 'preservatives'],
    'burning': ['alcohol', 'fragrance', 'acids', 'retinol'],
    'rash': ['fragrance', 'preservatives', 'dyes', 'sulfates'],
    'hives': ['fragrances', 'preservatives', 'proteins'],
    'swelling': ['fragrances', 'preservatives', 'proteins']
}

REMEDIES = {
    'fragrance': 'Switch to fragrance-free products. Apply aloe vera gel to soothe irritation.',
    'parabens': 'Use paraben-free products. Apply colloidal oatmeal to calm skin.',
    'sulfates': 'Choose sulfate-free cleansers. Use gentle, creamy cleansers instead.',
    'alcohol': 'Avoid alcohol-based products. Use hydrating, alcohol-free alternatives.',
    'retinol': 'Reduce retinol concentration or frequency. Always use sunscreen.',
}

# Helper Functions
def calculate_ingredient_features(ingredients_list):
    features = {
        'ingredient_count': len(ingredients_list),
        'high_risk_count': 0,
        'moderate_risk_count': 0,
        'comedogenic_count': 0,
        'irritant_count': 0,
        'beneficial_count': 0
    }
    
    for ing in ingredients_list:
        if any(harmful in ing for harmful in HARMFUL_INGREDIENTS['high_risk']):
            features['high_risk_count'] += 1
        if any(harmful in ing for harmful in HARMFUL_INGREDIENTS['moderate_risk']):
            features['moderate_risk_count'] += 1
        if any(harmful in ing for harmful in HARMFUL_INGREDIENTS['comedogenic']):
            features['comedogenic_count'] += 1
        if any(harmful in ing for harmful in HARMFUL_INGREDIENTS['irritants']):
            features['irritant_count'] += 1
        
        ing_data = INGREDIENT_DATA.get(ing, {})
        if ing_data.get('beneficial', False):
            features['beneficial_count'] += 1
    
    features['risk_score'] = (
        (features['high_risk_count'] * 3) + 
        (features['moderate_risk_count'] * 2) + 
        (features['comedogenic_count'] * 1.5) + 
        (features['irritant_count'] * 1)
    ) * 10
    features['risk_score'] = min(features['risk_score'], 100)
    
    if features['ingredient_count'] > 0:
        features['beneficial_score'] = (features['beneficial_count'] / features['ingredient_count'] * 100)
    else:
        features['beneficial_score'] = 0
    
    return features

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user = data['user_id']
        except:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Dermamon API is running! 🚀',
        'models_loaded': MODELS_LOADED,
        'database_connected': SUPABASE_CONNECTED,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/auth/signup', methods=['POST', 'OPTIONS'])
def signup():
    if request.method == 'OPTIONS':
        return '', 204
        
    if not SUPABASE_CONNECTED:
        return jsonify({'error': 'Database not connected'}), 503
        
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        response = supabase.table('users').insert({
            'email': email,
            'password': hashed_password.decode('utf-8'),
            'name': name,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        user_id = response.data[0]['id']
        
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user_id,
                'email': email,
                'name': name
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
        
    if not SUPABASE_CONNECTED:
        return jsonify({'error': 'Database not connected'}), 503
        
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        response = supabase.table('users').select('*').eq('email', email).execute()
        
        if not response.data:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user = response.data[0]
        
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(days=30)
        }, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name']
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET', 'PUT', 'OPTIONS'])
@token_required
def user_profile(current_user):
    if request.method == 'OPTIONS':
        return '', 204
        
    if not SUPABASE_CONNECTED:
        return jsonify({'error': 'Database not connected'}), 503
        
    try:
        if request.method == 'GET':
            response = supabase.table('users').select('id, email, name, profile_picture').eq('id', current_user).execute()
            
            if not response.data:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'success': True,
                'user': response.data[0]
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            update_data = {}
            
            if 'name' in data:
                update_data['name'] = data['name']
            if 'profile_picture' in data:
                update_data['profile_picture'] = data['profile_picture']
            
            response = supabase.table('users').update(update_data).eq('id', current_user).execute()
            
            return jsonify({
                'success': True,
                'user': response.data[0]
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        product_text = data.get('product', '').strip().lower()
        skin_type = data.get('skin_type', 'normal').lower()
        allergies = data.get('allergies', '').lower()
        
        if not product_text:
            return jsonify({'error': 'Product information required'}), 400
        
        # Check if it's a product name in database
        product_info = PRODUCT_DATABASE.get(product_text, None)
        
        if product_info:
            # Use product from database
            ingredients = [i.strip().lower() for i in product_info['ingredients'].split(',')]
            product_name = product_info['name']
            product_details = {
                'name': product_info['name'],
                'brand': product_info['brand'],
                'category': product_info['category'],
                'suitable_for': product_info['suitable_skin_types'],
                'concerns_addressed': product_info['concerns']
            }
        else:
            # Treat as ingredient list
            ingredients = [i.strip().lower() for i in product_text.split(',')]
            product_name = "Custom Product"
            product_details = None
        
        # Calculate features
        features = calculate_ingredient_features(ingredients)
        
        # ML Prediction
        feature_vector = [
            features['ingredient_count'],
            features['high_risk_count'],
            features['moderate_risk_count'],
            features['comedogenic_count'],
            features['irritant_count'],
            features['beneficial_count'],
            features['beneficial_score'],
            0, 0, 0
        ]
        
        ml_prediction = None
        ml_confidence = None
        
        if MODELS_LOADED:
            try:
                feature_scaled = risk_scaler.transform([feature_vector])
                prediction_encoded = risk_classifier.predict(feature_scaled)[0]
                ml_prediction = risk_encoder.inverse_transform([prediction_encoded])[0]
                
                if hasattr(risk_classifier, 'predict_proba'):
                    probas = risk_classifier.predict_proba(feature_scaled)[0]
                    ml_confidence = float(max(probas) * 100)
                else:
                    ml_confidence = 95.0
            except Exception as e:
                print(f"ML prediction error: {e}")
        
        # Risk calculation
        risk_score = features['risk_score']
        if risk_score < 20:
            risk_category = "Low"
            safe = True
        elif risk_score < 40:
            risk_category = "Moderate"
            safe = True
        else:
            risk_category = "High"
            safe = False
        
        if ml_prediction:
            risk_category = ml_prediction
            safe = risk_category in ['Low', 'Moderate']
        
        # Analyze ingredients
        high_risk = []
        moderate_risk = []
        beneficial = []
        allergy_warnings = []
        skin_warnings = []
        
        for ingredient in ingredients:
            ing_data = INGREDIENT_DATA.get(ingredient, {'risk': 30, 'beneficial': False})
            risk = ing_data['risk']
            
            if risk >= 50:
                high_risk.append(ingredient)
            elif risk >= 25:
                moderate_risk.append(ingredient)
            
            if ing_data['beneficial']:
                beneficial.append(ingredient)
            
            if allergies and ingredient in allergies:
                allergy_warnings.append(f"⚠️ Contains {ingredient} (you're allergic)")
            
            if skin_type in SKIN_TYPE_CONCERNS:
                if ingredient in SKIN_TYPE_CONCERNS[skin_type]:
                    skin_warnings.append(f"⚠️ {ingredient} may not be suitable for {skin_type} skin")
        
        # Recommendations
        recommendations = []
        if high_risk:
            recommendations.append(f"⚠️ Consider avoiding: {', '.join(high_risk[:3])}")
        if allergy_warnings:
            recommendations.append("🚫 Choose alternatives without your allergens")
        if len(beneficial) < len(ingredients) * 0.3:
            recommendations.append("💡 Look for products with more beneficial ingredients")
        
        recommendations.append("🧪 Always patch test new products")
        
        response_data = {
            'success': True,
            'product_name': product_name,
            'prediction': {
                'safe': safe,
                'risk_score': round(risk_score, 1),
                'risk_category': risk_category,
                'confidence': ml_confidence if ml_confidence else 87.5,
                'model_used': 'ML' if MODELS_LOADED and ml_prediction else 'Rule-based'
            },
            'analysis': {
                'total_ingredients': len(ingredients),
                'high_risk_count': len(high_risk),
                'moderate_risk_count': len(moderate_risk),
                'beneficial_count': len(beneficial),
                'high_risk_ingredients': high_risk,
                'beneficial_ingredients': beneficial,
                'all_ingredients': ingredients
            },
            'allergy_warnings': allergy_warnings,
            'skin_type_warnings': skin_warnings,
            'recommendations': recommendations,
            'skin_type_compatibility': '✅ Suitable' if not skin_warnings else '⚠️ Use with caution'
        }
        
        if product_details:
            response_data['product_details'] = product_details
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"Error in predict: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommend', methods=['POST', 'OPTIONS'])
def recommend():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        skin_type = data.get('skin_type', 'normal').lower()
        concern = data.get('concern', 'general').lower()
        
        concern_mapping = {
            'acne': 'acne',
            'aging': 'normal',
            'dryness': 'dry',
            'dark_spots': 'normal',
            'sensitivity': 'sensitive'
        }
        
        mapped_concern = concern_mapping.get(concern, skin_type)
        
        recommendations_db = {
            'dry': {
                'products': ['CeraVe Moisturizing Cream', 'La Roche-Posay Toleriane', 'Neutrogena Hydro Boost'],
                'ingredients': ['Hyaluronic Acid', 'Glycerin', 'Ceramides', 'Shea Butter']
            },
            'oily': {
                'products': ['Cetaphil Oil Control', 'La Roche-Posay Effaclar', 'Neutrogena Oil-Free'],
                'ingredients': ['Niacinamide', 'Salicylic Acid', 'Tea Tree Oil']
            },
            'sensitive': {
                'products': ['Vanicream Gentle Cleanser', 'CeraVe Hydrating Cleanser', 'Aveeno Ultra-Calming'],
                'ingredients': ['Colloidal Oatmeal', 'Centella Asiatica', 'Allantoin']
            },
            'acne': {
                'products': ['CeraVe SA Cleanser', 'Paula\'s Choice BHA', 'The Ordinary Niacinamide'],
                'ingredients': ['Salicylic Acid', 'Benzoyl Peroxide', 'Niacinamide', 'Tea Tree Oil']
            },
            'normal': {
                'products': ['CeraVe Daily Moisturizer', 'Neutrogena Gentle Cleanser', 'Simple Moisturizer'],
                'ingredients': ['Hyaluronic Acid', 'Vitamin E', 'Glycerin']
            }
        }
        
        result = recommendations_db.get(skin_type, recommendations_db.get(mapped_concern, recommendations_db['normal']))
        
        return jsonify({
            'success': True,
            'recommendations': result['products'],
            'beneficial_ingredients': result['ingredients'],
            'skin_type': skin_type,
            'concern': concern
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/allergy/analyze', methods=['POST', 'OPTIONS'])
def analyze_allergy():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', '').lower()
        suspected = data.get('suspected_ingredients', '').lower()
        image_data = data.get('image', None)
        
        # Validate: either symptoms or image must be provided
        if not symptoms and not image_data:
            return jsonify({'error': 'Either symptoms or image required'}), 400
        
        # Analyze symptoms
        likely_culprits = []
        if symptoms:
            for symptom, ingredients in ALLERGY_SYMPTOMS.items():
                if symptom in symptoms:
                    likely_culprits.extend(ingredients)
            likely_culprits = list(set(likely_culprits))
        
        # Get remedies
        remedies_list = []
        for culprit in likely_culprits:
            if culprit in REMEDIES:
                remedies_list.append({
                    'ingredient': culprit,
                    'remedy': REMEDIES[culprit]
                })
        
        # Real AI image analysis using Gemini
        image_analysis = None
        if image_data and GEMINI_API_KEY:
            try:
                # Decode Base64 to image
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                
                # Initialize Gemini model
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Create analysis prompt
                symptom_context = f"User reported symptoms: {symptoms}" if symptoms else "No symptoms described"
                suspected_context = f"Suspected ingredients: {suspected}" if suspected else ""
                
                prompt = f"""
                Analyze this skin condition image carefully.
                {symptom_context}
                {suspected_context}
                
                Provide a detailed dermatological analysis in this exact JSON format:
                {{
                    "severity": "mild/moderate/severe",
                    "type": "condition name (e.g., contact dermatitis, eczema, allergic reaction)",
                    "confidence": 85,
                    "observations": ["observation 1", "observation 2", "observation 3"],
                    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
                }}
                
                Be specific about visible symptoms like redness, swelling, texture changes, distribution pattern, etc.
                Provide practical, actionable recommendations.
                ONLY return valid JSON, no other text.
                """
                
                # Get AI analysis
                response = model.generate_content([prompt, image])
                
                # Parse response
                response_text = response.text.strip()
                
                # Clean up markdown code blocks if present
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                # Parse JSON
                image_analysis = json.loads(response_text)
                
                print(f"✅ Gemini analysis successful: {image_analysis['type']}")
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Response was: {response_text}")
                image_analysis = {
                    'severity': 'moderate',
                    'type': 'analysis incomplete',
                    'confidence': 50,
                    'observations': ['Image received but could not be fully analyzed', 'Please consult a dermatologist'],
                    'recommendations': ['Seek professional medical advice', 'Avoid scratching affected area']
                }
            except Exception as e:
                print(f"Gemini API error: {e}")
                image_analysis = {
                    'severity': 'unknown',
                    'type': 'analysis failed',
                    'confidence': 0,
                    'observations': ['Could not analyze image - API error'],
                    'recommendations': ['Please try again', 'Consult a dermatologist for accurate diagnosis']
                }
        elif image_data and not GEMINI_API_KEY:
            image_analysis = {
                'severity': 'unknown',
                'type': 'API key missing',
                'confidence': 0,
                'observations': ['Gemini API key not configured'],
                'recommendations': ['Add GEMINI_API_KEY to .env file']
            }
        
        # If no symptoms were provided but we have image analysis, try to extract likely culprits
        if not likely_culprits and image_analysis and image_analysis.get('observations'):
            # Basic extraction from observations
            likely_culprits = ['unknown allergen - see image analysis']
        
        # Default remedies if none found
        if not remedies_list:
            remedies_list = [{
                'ingredient': 'general',
                'remedy': 'Apply cool compress and use gentle, fragrance-free products'
            }]
        
        return jsonify({
            'success': True,
            'symptoms_detected': symptoms.split(',') if symptoms else ['analyzed from image'],
            'likely_culprits': likely_culprits if likely_culprits else ['See image analysis for details'],
            'remedies': remedies_list,
            'image_analysis': image_analysis,
            'general_advice': [
                '🩺 Stop using the suspected product immediately',
                '🧊 Apply cold compress to reduce inflammation',
                '💧 Use gentle, fragrance-free products',
                '👨‍⚕️ Consult a dermatologist if symptoms persist or worsen'
            ]
        })
    
    except Exception as e:
        print(f"Error in analyze_allergy: {e}")
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/api/reviews', methods=['POST', 'OPTIONS'])
@token_required
def add_review(current_user):
    if request.method == 'OPTIONS':
        return '', 204
        
    if not SUPABASE_CONNECTED:
        return jsonify({'error': 'Database not connected'}), 503
        
    try:
        data = request.get_json()
        
        response = supabase.table('reviews').insert({
            'user_id': current_user,
            'product_name': data.get('product_name'),
            'rating': data.get('rating'),
            'review_text': data.get('review_text'),
            'skin_type': data.get('skin_type'),
            'created_at': datetime.now().isoformat()
        }).execute()
        
        return jsonify({
            'success': True,
            'review': response.data[0]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reviews/<product_name>', methods=['GET'])
def get_reviews(product_name):
    if not SUPABASE_CONNECTED:
        return jsonify({'success': True, 'reviews': [], 'count': 0})
        
    try:
        response = supabase.table('reviews').select('*').eq('product_name', product_name).execute()
        
        return jsonify({
            'success': True,
            'reviews': response.data,
            'count': len(response.data)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# @app.route('/api/chat', methods=['POST', 'OPTIONS'])
# def chat():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        user_id = data.get('user_id', 'guest')
        
        responses = {
            'hello': 'Hi there! 👋 I\'m Dermamon, your skincare assistant. How can I help you today?',
            'hi': 'Hello! 😊 What would you like to know about skincare?',
            'help': 'I can help you with:\n• Product ingredient analysis\n• Skincare recommendations\n• Allergy warnings\n• Skin type advice\n\nJust ask me anything!',
            'acne': 'For acne-prone skin, I recommend looking for products with salicylic acid, niacinamide, or benzoyl peroxide. Avoid heavy oils like coconut oil. Would you like specific product recommendations?',
            'dry': 'For dry skin, look for ingredients like hyaluronic acid, glycerin, ceramides, and shea butter. Avoid alcohol and sulfates. Want me to recommend some products?',
            'sensitive': 'For sensitive skin, choose fragrance-free products with soothing ingredients like centella asiatica, colloidal oatmeal, and allantoin. Shall I suggest some gentle products?',
            'oily': 'For oily skin, look for lightweight, oil-free products with niacinamide, salicylic acid, and mattifying ingredients. Avoid heavy oils.','oily': 'For oily skin, look for lightweight, oil-free products with niacinamide, salicylic acid, and mattifying ingredients.',
            'product': 'Sure! I can help you analyze any product. Just tell me the product name or paste the ingredient list.',
            'recommend': 'I\'d be happy to recommend products! What\'s your skin type and main concern?',
            'game': '🎮 Want to play? Click on the game feature card on the homepage!',
        }
        
        bot_response = 'I\'m here to help with your skincare questions! Ask me about products, ingredients, or skin concerns.'
        for key in responses:
            if key in message:
                bot_response = responses[key]
                break
        
        return jsonify({
            'success': True,
            'response': bot_response
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/score', methods=['POST', 'OPTIONS'])
def save_game_score():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'guest')
        score = data.get('score', 0)
        game_type = data.get('game_type', 'balloon_hit')
        
        if SUPABASE_CONNECTED:
            try:
                supabase.table('game_scores').insert({
                    'user_id': user_id,
                    'score': score,
                    'game_type': game_type,
                    'created_at': datetime.now().isoformat()
                }).execute()
            except:
                pass
        
        return jsonify({
            'success': True,
            'score': score
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        if SUPABASE_CONNECTED:
            response = supabase.table('game_scores')\
                .select('*')\
                .order('score', desc=True)\
                .limit(10)\
                .execute()
            
            return jsonify({
                'success': True,
                'leaderboard': response.data
            })
        else:
            # Return mock data if database not connected
            return jsonify({
                'success': True,
                'leaderboard': [
                    {'user_id': 'Demo Player 1', 'score': 350},
                    {'user_id': 'Demo Player 2', 'score': 280},
                    {'user_id': 'Demo Player 3', 'score': 210}
                ]
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        original_message = data.get('message', '')  # Keep original case
        user_id = data.get('user_id', 'guest')
        
        print(f"📨 Chat request: {message}")
        print(f"🔑 Gemini available: {bool(GEMINI_API_KEY)}")
        
        # Build context from our knowledge base
        context_data = {
            'matched_products': [],
            'matched_ingredients': [],
            'skin_type_info': None,
            'symptoms_info': []
        }
        
        # Check products
        for product_key, product_info in PRODUCT_DATABASE.items():
            if product_key in message or any(word in message for word in product_key.split()):
                context_data['matched_products'].append(product_info)
        
        # Check ingredients
        for ingredient, ing_data in INGREDIENT_DATA.items():
            if ingredient in message:
                context_data['matched_ingredients'].append({
                    'name': ingredient,
                    'data': ing_data
                })
        
        # Check skin types
        for skin_type, concerns in SKIN_TYPE_CONCERNS.items():
            if skin_type in message:
                context_data['skin_type_info'] = {
                    'type': skin_type,
                    'avoid': concerns
                }
        
        # Check symptoms
        for symptom, culprits in ALLERGY_SYMPTOMS.items():
            if symptom in message:
                context_data['symptoms_info'].append({
                    'symptom': symptom,
                    'culprits': culprits
                })
        
        # Try Gemini AI first
        if GEMINI_API_KEY:
            try:
                print("🤖 Attempting Gemini response...")
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Build comprehensive system prompt
                system_prompt = """You are Dermamon 🧴, a friendly skincare expert AI assistant.

YOUR CORE KNOWLEDGE:

**PRODUCTS YOU KNOW:**
1. CeraVe Moisturizing Cream - For dry/sensitive skin, contains ceramides & hyaluronic acid
2. CeraVe Hydrating Cleanser - Gentle cleanser for dry/normal/sensitive skin
3. Neutrogena Hydro Boost Water Gel - Lightweight hydration for all skin types
4. La Roche-Posay Toleriane - For sensitive skin with niacinamide & ceramides
5. The Ordinary Niacinamide 10% + Zinc 1% - For oily/acne-prone skin
6. Cetaphil Oil Control - For oily skin
7. Paula's Choice BHA - Salicylic acid exfoliant for acne
8. Vanicream Gentle Cleanser - Ultra-gentle for sensitive skin
9. Aveeno Ultra-Calming - Soothes sensitive/irritated skin

**KEY INGREDIENTS:**
- Niacinamide: Brightening, oil control, pore minimizing (safe, risk 10/100)
- Hyaluronic Acid: Holds 1000x its weight in water (very safe, risk 5/100)
- Ceramides: Repair skin barrier, essential for dry/damaged skin (safe, risk 10/100)
- Salicylic Acid: Unclogs pores, treats acne (moderate risk 30/100)
- Retinol: Anti-aging but can irritate (higher risk 40/100)
- Vitamin C: Brightening, antioxidant (low risk 15/100)
- Glycerin: Humectant, draws moisture (very safe, risk 5/100)

**HARMFUL TO AVOID:**
- Parabens (risk 70/100): Hormone disruptors
- Sulfates/SLS (risk 65/100): Harsh, strip natural oils
- Fragrance/Parfum (risk 60/100): Common allergen
- Alcohol Denat (risk 50/100): Very drying

**SKIN TYPE RECOMMENDATIONS:**
- Dry Skin: Hyaluronic acid, ceramides, glycerin, shea butter. Avoid alcohol & sulfates.
  Best: CeraVe Moisturizing Cream, La Roche-Posay Toleriane, Neutrogena Hydro Boost
  
- Oily Skin: Niacinamide, salicylic acid, lightweight gels. Avoid heavy oils.
  Best: The Ordinary Niacinamide, Neutrogena Hydro Boost, Cetaphil Oil Control, Paula's Choice BHA
  
- Sensitive Skin: Fragrance-free, minimal ingredients, soothing. Avoid fragrance, alcohol, sulfates.
  Best: La Roche-Posay Toleriane, CeraVe Hydrating Cleanser, Vanicream, Aveeno Ultra-Calming
  
- Acne-Prone: Salicylic acid, niacinamide, benzoyl peroxide. Avoid coconut oil.
  Best: The Ordinary Niacinamide, Paula's Choice BHA, CeraVe SA Cleanser

**PRODUCT-SPECIFIC INFO:**
- Vaseline (Petrolatum): EXCELLENT for dry skin as an occlusive (locks in moisture). NOT recommended for oily/acne-prone skin as it's very heavy and can clog pores.

**YOUR PERSONALITY:**
- Friendly and enthusiastic about skincare
- Use 1-2 emojis per response
- Keep responses concise (3-5 sentences)
- Be specific with product names when asked
- Always back up recommendations with reasoning
- Encourage trying the "Product Analysis" feature for detailed checks

**RESPONSE RULES:**
- If asked for "options" or "more" products, give 3-5 specific product names
- If asked about a product, explain its benefits and suitability
- If asked about skin type, recommend specific products for that type
- Be conversational but informative
- Don't just repeat the same response - expand with new information
"""

                # Add context from our database if relevant
                context_addon = ""
                if context_data['matched_products']:
                    context_addon += "\n**RELEVANT PRODUCTS USER MIGHT BE ASKING ABOUT:**\n"
                    for prod in context_data['matched_products'][:2]:
                        context_addon += f"- {prod['name']}: {', '.join(prod['suitable_skin_types'])} skin\n"
                
                if context_data['skin_type_info']:
                    st = context_data['skin_type_info']
                    context_addon += f"\n**USER ASKED ABOUT {st['type'].upper()} SKIN**\n"
                    context_addon += f"Should avoid: {', '.join(st['avoid'][:3])}\n"
                
                full_prompt = f"{system_prompt}\n{context_addon}\n\nUser: {original_message}\n\nDermamon (respond naturally and specifically):"
                
                response = model.generate_content(full_prompt)
                bot_response = response.text.strip()
                
                # Add feature suggestion if relevant
                if any(word in message for word in ['analyze', 'check', 'ingredients', 'safe']):
                    if 'Product Analysis' not in bot_response:
                        bot_response += "\n\n💡 Want a detailed safety check? Click 'Product Analysis'!"
                
                print(f"✅ Gemini response generated successfully")
                
                return jsonify({
                    'success': True,
                    'response': bot_response,
                    'powered_by': 'Gemini AI'
                })
                
            except Exception as e:
                print(f"❌ Gemini error: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue to fallback
        else:
            print("⚠️ Gemini API key not available, using fallback")
        
        # Fallback responses
        print("📝 Using fallback responses")
        
        # Check for product match first
        if context_data['matched_products']:
            prod = context_data['matched_products'][0]
            bot_response = f"**{prod['name']}** is great! 🧴\n\n"
            bot_response += f"✨ Perfect for {', '.join(prod['suitable_skin_types'])} skin\n"
            bot_response += f"🔑 Key ingredients: {', '.join(prod['ingredients'].split(',')[:3])}\n"
            bot_response += f"🎯 Addresses: {', '.join(prod['concerns'][:2])}\n\n"
            bot_response += "Want a full ingredient analysis? Click 'Product Analysis'!"
            
            return jsonify({
                'success': True,
                'response': bot_response,
                'powered_by': 'Dermamon Database'
            })
        
        # Specific product recommendations
        if any(word in message for word in ['option', 'more', 'recommend', 'suggest', 'product name']):
            if 'oily' in message or 'acne' in message:
                bot_response = """For oily/acne-prone skin, try these: 🎯

1. **The Ordinary Niacinamide 10% + Zinc 1%** - Controls oil, minimizes pores
2. **Neutrogena Hydro Boost Water Gel** - Lightweight, oil-free hydration
3. **Cetaphil Oil Control** - Mattifying moisturizer
4. **Paula's Choice 2% BHA** - Exfoliates, unclogs pores
5. **La Roche-Posay Effaclar** - Oil control & acne treatment

Want to check if any of these are safe for you? Use 'Product Analysis'! 💡"""
            
            elif 'dry' in message:
                bot_response = """For dry skin, these are perfect: 💧

1. **CeraVe Moisturizing Cream** - Rich, with ceramides & hyaluronic acid
2. **La Roche-Posay Toleriane** - Gentle, repairs barrier
3. **Neutrogena Hydro Boost** - Lightweight but hydrating
4. **Vanicream Moisturizing Cream** - Ultra-gentle, fragrance-free
5. **Aveeno Eczema Therapy** - Soothes very dry skin

All of these are dermatologist-recommended! Want detailed analysis? 🔍"""
            
            elif 'sensitive' in message:
                bot_response = """For sensitive skin, use these gentle options: 🛡️

1. **La Roche-Posay Toleriane** - Minimal ingredients, very gentle
2. **Vanicream Gentle Cleanser** - Fragrance-free, hypoallergenic
3. **CeraVe Hydrating Cleanser** - Non-irritating, maintains barrier
4. **Aveeno Ultra-Calming** - Soothes redness & irritation
5. **Cetaphil Gentle Cleanser** - Dermatologist favorite

All fragrance-free and clinically tested! Need ingredient breakdown? 📊"""
            
            else:
                bot_response = """Here are some top-rated options: ✨

**For Hydration:**
- Neutrogena Hydro Boost
- CeraVe Moisturizing Cream

**For Acne:**
- The Ordinary Niacinamide
- Paula's Choice BHA

**For Sensitivity:**
- La Roche-Posay Toleriane
- Vanicream Gentle Cleanser

What's your skin type? I can narrow it down! 🎯"""
            
            return jsonify({
                'success': True,
                'response': bot_response,
                'powered_by': 'Dermamon Database'
            })
        
        # Vaseline specific
        if 'vaseline' in message:
            if 'dry' in message:
                bot_response = "Yes! Vaseline (petrolatum) is EXCELLENT for dry skin! 💧 It works as an occlusive - meaning it locks moisture into your skin. Apply it over a moisturizer for best results. It's very safe and effective for very dry, chapped skin. Not recommended for face if you have oily/acne-prone skin though!"
            elif 'oily' in message or 'acne' in message:
                bot_response = "Not ideal for oily/acne-prone skin! ⚠️ Vaseline is very occlusive and heavy, which can clog pores and worsen breakouts. For oily skin, try lightweight gel moisturizers like Neutrogena Hydro Boost or The Ordinary Niacinamide instead! 🎯"
            else:
                bot_response = "Vaseline (petrolatum) is great for dry skin as it locks in moisture! 💧 However, it's too heavy for oily or acne-prone skin. What's your skin type? I can recommend better alternatives! 🧴"
            
            return jsonify({
                'success': True,
                'response': bot_response,
                'powered_by': 'Dermamon Database'
            })
        
        # General responses
        responses = {
            'hello': 'Hi! 👋 I\'m Dermamon, your skincare expert. What would you like to know?',
            'hi': 'Hello! 😊 Ask me about products, ingredients, or your skin concerns!',
            'help': 'I can help with:\n• Product recommendations\n• Ingredient analysis\n• Skin type advice\n• Allergy detection\n\nWhat interests you? 💡',
            'thank': 'You\'re welcome! 😊 Always happy to help with skincare!',
        }
        
        for key, value in responses.items():
            if key in message:
                return jsonify({
                    'success': True,
                    'response': value,
                    'powered_by': 'Dermamon'
                })
        
        # Default
        bot_response = "I\'m here to help with skincare! 🧴 Ask me about specific products, ingredients, or your skin concerns. What would you like to know?"
        
        return jsonify({
            'success': True,
            'response': bot_response,
            'powered_by': 'Dermamon'
        })
    
    except Exception as e:
        print(f"💥 Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/api/debug/status', methods=['GET'])
def debug_status():
    return jsonify({
        'gemini_key_loaded': bool(GEMINI_API_KEY),
        'gemini_key_length': len(GEMINI_API_KEY) if GEMINI_API_KEY else 0,
        'models_loaded': MODELS_LOADED,
        'database_connected': SUPABASE_CONNECTED
    })
    
if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting Dermamon API...")
    print("="*50)
    print(f"📊 Models: {'✅' if MODELS_LOADED else '⚠️ No'}")
    print(f"🔗 Database: {'✅' if SUPABASE_CONNECTED else '⚠️ No'}")
    print(f"🌍 Server: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)