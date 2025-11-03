from flask import Flask, render_template
import threading
import pandas as pd
import os
import joblib
from pyngrok import ngrok

APP_DIR = "/content/Medical_app"   # adjust if needed
CSV_PATH = os.path.join(APP_DIR, "health_data_labeled.csv")
MODEL_PATH = os.path.join(APP_DIR, "isolation_forest_model.pkl")

app = Flask(__name__, template_folder=os.path.join(APP_DIR, "templates"))

def ensure_model():
    # load if exists, else try to train a quick one
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print("✅ Loaded model from", MODEL_PATH)
        return model
    else:
        # quick fallback training (safe, uses health_data.csv or health_data_labeled.csv)
        print("⚠️ Model file not found. Training quick fallback model...")
        data_csv = os.path.join(APP_DIR, "health_data.csv")
        if not os.path.exists(data_csv):
            # try labeled CSV
            data_csv = CSV_PATH
            if not os.path.exists(data_csv):
                raise FileNotFoundError("No data CSV found to train fallback model.")
        df = pd.read_csv(data_csv)
        X = df[["heart_rate","blood_oxygen"]].dropna().values
        from sklearn.ensemble import IsolationForest
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(X)
        joblib.dump(model, MODEL_PATH)
        print("✅ Fallback model trained and saved to", MODEL_PATH)
        return model

model = ensure_model()

def recommend_from_row(hr, oxy):
    # concise, immediately actionable advice
    if hr > 120:
        return "⚠️ High HR >120: Seek immediate medical attention."
    if hr > 100:
        return "⚠️ Elevated HR: Rest, slow breathing; consider medical review if persistent."
    if hr < 50:
        return "⚠️ Low HR: Sit/lie down, seek medical review if symptomatic."
    if oxy < 92:
        return "⚠️ Low SpO₂: Seek medical attention; consider supplemental oxygen if prescribed."
    if oxy < 95:
        return "⚠️ Mild dip in SpO₂: Breathe slowly; recheck in a few minutes."
    return "✅ Vitals look ok. Continue normal activity and monitoring."

@app.route('/')
def home():
    if not os.path.exists(CSV_PATH):
        return "Data file not found. Run simulate_data.py or upload health_data_labeled.csv", 500

    df = pd.read_csv(CSV_PATH)
    # guard if file empty
    if df.empty:
        return "No data available yet. Run simulator to generate rows.", 500

    latest = df.iloc[-1].to_dict()

    # Prepare features for model (order must match training)
    features = [[latest.get("heart_rate"), latest.get("blood_oxygen")]]

    # model prediction: -1 = anomaly, 1 = normal
    pred = model.predict(features)[0]
    score = None
    try:
        # decision_function: larger -> more normal, smaller -> more anomalous (negative)
        score = float(model.decision_function(features)[0])
    except Exception:
        score = None

    status = "Anomaly" if pred == -1 else "Normal"
    recommendation = recommend_from_row(latest.get("heart_rate", 0), latest.get("blood_oxygen", 0))

    # pass everything into template
    return render_template("index.html",
                           data=latest,
                           model_status=status,
                           model_score=score,
                           recommendation=recommendation)

def run():
    app.run(port=5000, use_reloader=False)

if __name__ == "__main__":
    public_url = ngrok.connect(5000)
    print("🚀 App is live at:", public_url)
    threading.Thread(target=run).start()
