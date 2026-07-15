@echo off
echo Creating requirements.txt...
(
echo flask==2.3.2
echo flask-cors==4.0.0
echo nltk==3.8.1
echo scikit-learn==1.3.0
echo pandas==2.0.3
echo numpy==1.24.3
echo joblib==1.3.2
echo gunicorn==21.2.0
) > requirements.txt

echo Installing packages...
python -m pip install -r requirements.txt

echo Starting app...
python app.py
pause