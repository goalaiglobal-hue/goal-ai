from flask import Flask, jsonify, request, render_template
import os
import requests

app = Flask(__name__)

# Direct fallback configuration so it never fails on Termux or Render
SUPABASE_URL = os.environ.get("SUPABASE_URL") or "https://aybfoxieispekcoedvjzho.supabase.co"
SUPABASE_URL = SUPABASE_URL.rstrip("/")
if not SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL += "/rest/v1"

SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # Apni Supabase anon key yahan paste kar sakte ho

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
        data = r.json()
        if isinstance(data, list):
            cleaned_data = []
            for item in data:
                text = item.get("goal") or item.get("title") or item.get("text") or "Untitled Goal"
                cleaned_data.append({
                    "id": item.get("id"),
                    "goal": text,
                    "title": text,
                    "category": item.get("category", "General"),
                    "progress": item.get("progress", 0)
                })
            return jsonify(cleaned_data), 200
        return jsonify(data), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/goals", methods=["POST"])
def add_goal():
    data = request.get_json() or {}
    goal_text = data.get("goal") or data.get("title") or data.get("message")
    
    if not goal_text:
        return jsonify({"error": "Goal text missing!"}), 400

    payload = {
        "goal": goal_text
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
        res_data = r.json()
        return jsonify(res_data), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/goals/<int:goal_id>", methods=["PATCH"])
def update_goal(goal_id):
    data = request.get_json() or {}
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

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    user_prompt = data.get("message", "") or data.get("prompt", "")
    response_text = f"Goal AI Received: {user_prompt}"
    return jsonify({
        "response": response_text,
        "status": "success"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
