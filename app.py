import os
import re
import joblib
import nltk
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

app = Flask(__name__)
CORS(app)

for pkg in ['punkt', 'punkt_tab', 'stopwords', 'wordnet']:
    nltk.download(pkg, quiet=True)

_lemmatizer = WordNetLemmatizer()
_stop_words  = set(stopwords.words('english'))

def preprocess(text):
    text   = text.lower()
    text   = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in _stop_words]
    tokens = [_lemmatizer.lemmatize(t) for t in tokens]
    return ' '.join(tokens)

# Load model — trained during build, not at runtime
print("Loading model...")
classifier = joblib.load('models/classifier.pkl')
vectorizer = joblib.load('models/vectorizer.pkl')
print("Model loaded.")

@app.route('/')
def index():
    return render_template('index.html', best_model='Logistic Regression')

@app.route('/predict', methods=['POST'])
def predict():
    data    = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    if len(message) > 1000:
        return jsonify({'error': 'Message too long'}), 400

    processed  = preprocess(message)
    vec        = vectorizer.transform([processed])
    label      = classifier.predict(vec)[0]
    confidence = None

    if hasattr(classifier, 'predict_proba'):
        proba      = classifier.predict_proba(vec)[0]
        classes    = list(classifier.classes_)
        fraud_prob = proba[classes.index('fraud')]
        confidence = round(float(fraud_prob if label == 'fraud' else 1 - fraud_prob) * 100, 1)

    return jsonify({
        'label':      label,
        'is_fraud':   label == 'fraud',
        'confidence': confidence,
        'message':    message,
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
