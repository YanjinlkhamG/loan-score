import warnings
warnings.filterwarnings('ignore')

from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
import os

app = Flask(__name__)

# Load model pipeline
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'loan_scoring_model.pkl')
data = joblib.load(MODEL_PATH)

model       = data['model']
scaler      = data['scaler']
le_emp      = data['label_encoder_employment']
le_dec      = data['label_encoder_decision']
feature_cols = data['feature_cols']

EMPLOYMENT_TYPES = list(le_emp.classes_)


def compute_score(monthly_income, employment_years, requested_amount, employment_type):
    """
    Returns (score 0-1000, decision str, proba dict).
    Score formula:  (P_approved * 0.7 + P_manual * 0.35) * 1000
    which gives ≈700+ for clear approvals, ≈350-500 for borderline, <350 for rejections.
    Then we linearly rescale to keep the thresholds at 700/450 as requested.
    """
    emp_encoded = le_emp.transform([employment_type])[0]
    ratio       = requested_amount / monthly_income if monthly_income > 0 else 0
    annual_dti  = ratio / 12
    log_income  = np.log1p(monthly_income)
    log_amount  = np.log1p(requested_amount)

    X = np.array([[
        monthly_income, employment_years, requested_amount,
        ratio, annual_dti, log_income, log_amount, emp_encoded
    ]])
    X_scaled = scaler.transform(X)

    pred_class  = model.predict(X_scaled)[0]
    pred_proba  = model.predict_proba(X_scaled)[0]
    decision    = le_dec.inverse_transform([pred_class])[0]

    p_app, p_man, p_rej = pred_proba[0], pred_proba[1], pred_proba[2]

    # Weighted score: approved pulls toward 1000, rejected pulls toward 0
    raw_score = (p_app * 0.7 + p_man * 0.35) * 1000   # max ≈700 for pure approval
    # Rescale so that raw 700 → 1000, raw 0 → 0  (linear stretch)
    score = int(min(1000, max(0, round(raw_score / 700 * 1000))))

    proba = {
        'approved': round(float(p_app) * 100, 1),
        'manual_review': round(float(p_man) * 100, 1),
        'rejected': round(float(p_rej) * 100, 1),
    }
    return score, decision, proba


@app.route('/')
def index():
    return render_template('index.html', employment_types=EMPLOYMENT_TYPES)


@app.route('/predict', methods=['POST'])
def predict():
    try:
        monthly_income     = float(request.form['monthly_income'])
        employment_years   = float(request.form['employment_years'])
        requested_amount   = float(request.form['requested_amount'])
        employment_type    = request.form['employment_type']

        if monthly_income <= 0 or requested_amount <= 0 or employment_years < 0:
            return jsonify({'error': 'Утгууд тэгээс их байх ёстой.'}), 400

        if employment_type not in EMPLOYMENT_TYPES:
            return jsonify({'error': 'Мэргэжил олдсонгүй.'}), 400

        score, decision, proba = compute_score(
            monthly_income, employment_years, requested_amount, employment_type
        )

        if score >= 700:
            verdict = 'approved'
            verdict_mn = 'Зөвшөөрөгдсөн'
        elif score >= 450:
            verdict = 'manual'
            verdict_mn = 'Гар шалгалт'
        else:
            verdict = 'rejected'
            verdict_mn = 'Татгалзсан'

        return jsonify({
            'score': score,
            'verdict': verdict,
            'verdict_mn': verdict_mn,
            'model_decision': decision,
            'proba': proba,
            'ratio': round(requested_amount / monthly_income, 1) if monthly_income else 0
        })

    except (ValueError, KeyError) as e:
        return jsonify({'error': f'Оролтын алдаа: {e}'}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
