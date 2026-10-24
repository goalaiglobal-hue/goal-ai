from flask import Flask, jsonify, request, render_template
import os
import requests

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL") or "https://aybfoxieispekcoedvjzho.supabase.co"
SUPABASE_URL = SUPABASE_URL.rstrip("/")
if not SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL += "/rest/v1"

SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

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
            cleaned = []
            for item in data:
                text = item.get("goal") or item.get("title") or item.get("text") or "Goal"
                cleaned.append({
                    "id": item.get("id"),
                    "goal": text,
                    "title": text
                })
            return jsonify(cleaned), 200
        return jsonify([]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/goals", methods=["POST"])
def add_goal():
    data = request.get_json() or {}
    goal_text = data.get("goal") or data.get("title") or data.get("message")
    
    if not goal_text:
        return jsonify({"error": "Goal text missing!"}), 400

    payload = {"goal": goal_text}

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
        if isinstance(res_data, list) and len(res_data) > 0:
            item = res_data[0]
            item["title"] = item.get("goal", goal_text)
            return jsonify(item), 200
        return jsonify({"id": 1, "goal": goal_text, "title": goal_text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    user_prompt = data.get("message", "") or data.get("prompt", "")
    return jsonify({
        "response": f"Goal AI Received: {user_prompt}",
        "status": "success"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
