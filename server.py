
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

ALLOWED_ORIGIN = "https://platinumphysiotherapyit-crypto.github.io"

STEP_NAMES = {
    1: "Account Awareness",
    2: "PIN Security Awareness",
    3: "Transaction Safety",
    4: "OTP Security Awareness",
    5: "Training Completed"
}


@app.after_request
def add_headers(response):
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/step", methods=["POST", "OPTIONS"])
def save_step():
    if request.method == "OPTIONS":
        return "", 204

    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"error": "Server configuration missing"}), 500

    data = request.get_json(silent=True) or {}

    user_id = data.get("demo_user_id")
    step = data.get("step_number")
    result = data.get("quiz_result")

    if not isinstance(user_id, str) or not user_id.strip():
        return jsonify({"error": "Demo ID required"}), 400

    if type(step) is not int or step not in STEP_NAMES:
        return jsonify({"error": "Invalid step"}), 400

    if result not in ["Correct", "Incorrect", "Not attempted"]:
        return jsonify({"error": "Invalid quiz result"}), 400

    record = {
        "demo_user_id": user_id.strip()[:60],
        "training_module": "Security Awareness Training",
        "step_number": step,
        "step_name": STEP_NAMES[step],
        "quiz_result": result,
        "completion_status": "Completed"
    }

    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/training_records",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            json=record,
            timeout=15
        )

        if r.status_code not in (200, 201, 204):
    print("SUPABASE ERROR:", r.status_code, r.text)
    return jsonify({
        "error": "Record could not be saved",
        "status": r.status_code
    }), 502

        return jsonify({"success": True, "step": step}), 201

    except requests.RequestException:
        return jsonify({"error": "Database connection failed"}), 502


@app.route("/api/events", methods=["GET"])
def get_events():
    if not ADMIN_TOKEN:
        return jsonify({"error": "Admin access not configured"}), 503

    supplied_token = request.headers.get("Authorization", "")
    if supplied_token != f"Bearer {ADMIN_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/training_records",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            },
            params={
                "select": "demo_user_id,step_number,step_name,quiz_result,completion_status,completed_at",
                "order": "completed_at.desc",
                "limit": "100"
            },
            timeout=15
        )

        if r.status_code != 200:
            return jsonify({"error": "Database read failed"}), 502

        return jsonify(r.json())

    except requests.RequestException:
        return jsonify({"error": "Database connection failed"}), 502


@app.route("/")
def home():
    return jsonify({
        "service": "Ethical Security Awareness Training API",
        "status": "running"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
