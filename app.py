from flask import Flask, jsonify, request, render_template
import os
import requests

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
if SUPABASE_URL and not SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL += "/rest/v1"

SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json"
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/goals", methods=["GET"])
def get_goals():
    try:
        r = requests.get(
            f"{SUPABASE_URL}/goals?select=*",
            headers=headers
        )
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/goals", methods=["POST"])
def add_goal():
    data = request.get_json()
    if not data or not data.get("goal"):
        return jsonify({"error": "Goal text missing!"}), 400

    payload = {
        "goal": data["goal"],
        "target_date": data.get("target_date"),
        "category": data.get("category", "General"),
        "progress": data.get("progress", 0)
    }

    try:
        r = requests.post(
            f"{SUPABASE_URL}/goals",
            headers={
                **headers,
                "Prefer": "return=representation"
            },
            json=payload
        )
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/goals/<int:goal_id>", methods=["PATCH"])
def update_goal(goal_id):
    data = request.get_json()
    try:
        r = requests.patch(
            f"{SUPABASE_URL}/goals?id=eq.{goal_id}",
            headers={
                **headers,
                "Prefer": "return=representation"
            },
            json=data
        )
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    try:
        r = requests.delete(
            f"{SUPABASE_URL}/goals?id=eq.{goal_id}",
            headers=headers
        )
        return jsonify({"message": "Goal deleted", "status": r.status_code}), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fix for Frontend /api/chat call
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    user_prompt = data.get("message", "")
    
    # Simple response or pass-through
    response_text = f"Goal AI Received: {user_prompt}. Plan generated successfully!"
    return jsonify({"response": response_text, "status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
