import os
import re
import random
import joblib
import nltk
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.calibration import CalibratedClassifierCV

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

FRAUD_TEMPLATES = [
    "Dear customer your MTN MoMo account will be suspended within 24 hours Click here to verify {link}",
    "Congratulations You have won GHS {amount} from MTN MoMo promo Call {phone} to claim your prize",
    "URGENT Your MoMo wallet has been flagged for suspicious activity Verify your PIN immediately at {link}",
    "Alert GHS {amount} has been debited from your account If you did not authorise this call {phone}",
    "Your MTN MoMo verification code is required to process your transaction Please reply with your PIN",
    "Dear valued customer your MoMo account will be deactivated Call {phone} now to prevent suspension",
    "You have been selected as winner in our MTN loyalty promo Claim GHS {amount} now call {phone}",
    "Security alert Your MoMo PIN has been compromised Click {link} to secure your account now",
    "Ghana Revenue Authority Your tax refund of GHS {amount} is ready Provide your MoMo PIN to receive",
    "FINAL NOTICE Your MoMo account shows unauthorised login Verify identity at {link} or lose access",
    "Congratulations Your number won GHS {amount} in Telecel monthly draw Contact {phone} to claim",
    "Dear MoMo user your wallet will be blocked due to inactivity Send your PIN to {phone} to reactivate",
    "MTN Ghana Your account requires immediate verification to avoid suspension Click {link} immediately",
    "Alert Unauthorised debit of GHS {amount} from your account Call {phone} to reverse transaction now",
    "You have a pending reward of GHS {amount} from Fidelity Bank Provide your MoMo details at {link}",
    "URGENT Ecobank Ghana Your linked MoMo account is compromised Verify details at {link} now",
    "GCB Bank Your linked MoMo wallet shows suspicious activity Call {phone} immediately",
    "Claim your free airtime of GHS {amount} by sending your PIN to {phone} today",
    "Your MoMo account has been temporarily suspended due to fraud risk Restore access call {phone}",
    "Telecel Ghana Congratulations you won airtime GHS {amount} Share your PIN to receive reward",
    "Attention your MoMo account will be closed verify urgently at {link} to avoid loss",
    "AirtelTigo Your account requires urgent verification Reply with OTP to avoid interruption",
    "Claim your MoMo cashback of GHS {amount} today limited time offer call {phone} now",
    "Warning account blocked contact {phone} immediately to restore your MoMo service",
    "Dear winner You have been selected for GHS {amount} MoMo cash prize Send PIN to claim",
    "Your MoMo transfer of GHS {amount} is pending confirm your PIN at {link} to complete",
    "MTN MoMo Promotional bonus of GHS {amount} available Send your account details to {phone}",
    "Verify your MoMo account now or lose access permanently click {link} before midnight",
    "Congratulations lucky customer GHS {amount} MoMo reward waiting Call {phone} to collect",
    "Your account has been flagged for review provide PIN at {link} to restore full access",
]

HAM_TEMPLATES = [
    "You have received GHS {amount} from {phone} Your new MoMo balance is GHS {balance}",
    "Your MoMo balance is GHS {balance} Thank you for using MTN Mobile Money",
    "Your MoMo account has been credited with GHS {amount} Transaction ID {txn_id}",
    "You have successfully sent GHS {amount} to {phone} Your balance is GHS {balance}",
    "MTN MoMo Transaction confirmed GHS {amount} paid to {merchant} Balance GHS {balance}",
    "Your MoMo account has been debited GHS {amount} for electricity bill Transaction {txn_id}",
    "Cash out successful GHS {amount} withdrawn at agent {phone} Balance GHS {balance}",
    "Top up successful GHS {amount} added to your MoMo wallet New balance GHS {balance}",
    "You have received airtime worth GHS {amount} on your MTN line Thank you",
    "Bundle purchase successful You now have {amount}GB data valid for 30 days",
    "Telecel Ghana Your account has been credited with GHS {amount} Ref {txn_id}",
    "AirtelTigo Money You sent GHS {amount} to {phone} Charge GHS 1 Balance GHS {balance}",
    "Merchant payment GHS {amount} to {merchant} approved Transaction ID {txn_id}",
    "Your MoMo savings interest of GHS {amount} has been credited Thank you",
    "Bill payment successful GHS {amount} paid to ECG for meter {txn_id}",
    "Loan repayment of GHS {amount} received Thank you for banking with us",
    "Insurance premium GHS {amount} deducted from MoMo wallet Policy active",
    "Transfer reversal GHS {amount} credited back to your account Ref {txn_id}",
    "MTN MoMo You have successfully deposited GHS {amount} Balance GHS {balance}",
    "Your MoMo account statement Balance GHS {balance} Available GHS {balance}",
    "Confirmation Your MoMo payment of GHS {amount} to {merchant} was successful",
    "GHS {amount} sent to {phone} successfully New balance GHS {balance} Thank you",
    "Your MTN data bundle of {amount}GB activated successfully Enjoy browsing",
    "Transaction successful Reference {txn_id} Amount GHS {amount} Balance GHS {balance}",
    "You have received a MoMo transfer of GHS {amount} from {merchant} Balance GHS {balance}",
    "MTN bill payment GHS {amount} for DSTV subscription successful Ref {txn_id}",
    "Airtime purchase of GHS {amount} for {phone} was successful Thank you",
    "Your MoMo wallet has been successfully activated Welcome to MTN Mobile Money",
    "Cash deposit of GHS {amount} received Thank you for banking with us Balance GHS {balance}",
    "Monthly statement Your MoMo account balance is GHS {balance} as of today",
]

def fill(template):
    return template.format(
        amount   = random.choice(['50','100','200','500','1000','2000','5000']),
        balance  = str(random.randint(50, 5000)),
        phone    = random.choice(['024XXXXXXX','055XXXXXXX','059XXXXXXX','0549XXXXXX']),
        txn_id   = str(random.randint(100000000, 999999999)),
        link     = random.choice(['bit.ly/mtn-verify','mtn-gh.net/verify','momogh.co/claim']),
        merchant = random.choice(['Shoprite','Melcom','KFC','Game Store','Electromart']),
    )

def build_dataset(n=600):
    rows = (
        [{'message': fill(random.choice(FRAUD_TEMPLATES)), 'label': 'fraud'} for _ in range(n)] +
        [{'message': fill(random.choice(HAM_TEMPLATES)),   'label': 'ham'}   for _ in range(n)]
    )
    return pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)

MODEL_DIR = 'models'
CLF_PATH  = os.path.join(MODEL_DIR, 'classifier.pkl')
VEC_PATH  = os.path.join(MODEL_DIR, 'vectorizer.pkl')

def train():
    print("Building dataset...")
    df = build_dataset(600)
    df['processed'] = df['message'].apply(preprocess)

    X_train, X_test, y_train, y_test = train_test_split(
        df['processed'], df['label'],
        test_size=0.2, random_state=42, stratify=df['label']
    )

    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.8
    )
    X_train_v = vectorizer.fit_transform(X_train)
    X_test_v  = vectorizer.transform(X_test)

    candidates = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Multinomial NB':      MultinomialNB(alpha=1.0),
        'SVM (Linear)':        CalibratedClassifierCV(LinearSVC(random_state=42)),
    }

    best_model, best_acc, best_name = None, 0, ''
    results = {}

    for name, clf in candidates.items():
        clf.fit(X_train_v, y_train)
        y_pred = clf.predict(X_test_v)
        acc  = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, pos_label='fraud')
        rec  = recall_score(y_test, y_pred, pos_label='fraud')
        f1   = f1_score(y_test, y_pred, pos_label='fraud')
        results[name] = {'accuracy': round(acc,4), 'precision': round(prec,4),
                         'recall': round(rec,4), 'f1': round(f1,4)}
        print(f"  {name}: Acc={acc:.4f} Prec={prec:.4f} Rec={rec:.4f} F1={f1:.4f}")
        if acc > best_acc:
            best_acc, best_model, best_name = acc, clf, name

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(best_model, CLF_PATH)
    joblib.dump(vectorizer, VEC_PATH)
    print(f"Best model: {best_name} ({best_acc*100:.2f}%)")
    return results, best_name

if os.path.exists(CLF_PATH) and os.path.exists(VEC_PATH):
    print("Loading saved model...")
    classifier = joblib.load(CLF_PATH)
    vectorizer = joblib.load(VEC_PATH)
    _metrics, _best_name = {}, "Logistic Regression"
else:
    print("Training model...")
    _metrics, _best_name = train()
    classifier = joblib.load(CLF_PATH)
    vectorizer = joblib.load(VEC_PATH)

@app.route('/')
def index():
    return render_template('index.html', best_model=_best_name)

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