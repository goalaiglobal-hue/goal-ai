from flask import Flask, render_template, request, jsonify
import requests
import os
import json

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

# Fallback in case environment variables are not exported in shell
if not SUPABASE_URL:
    SUPABASE_URL = "https://your-supabase-url.supabase.co" # Ya apni Supabase URL yahan paste karein

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def generate_roadmap_with_gemini(goal_title):
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return ["Set clear targets", "Create an execution plan", "Review progress daily"]
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    prompt = f"Create a short, actionable 3 to 5 step roadmap for the goal: '{goal_title}'. Return ONLY a JSON array of strings, for example: [\"Step 1\", \"Step 2\", \"Step 3\"]."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        if "candidates" in data and data["candidates"]:
            ai_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            if ai_text.startswith("```"):
                ai_text = ai_text.split("```")[1]
                if ai_text.startswith("json"):
                    ai_text = ai_text[4:].strip()
            return json.loads(ai_text)
        else:
            return ["Define goal milestone", "Execute step 1", "Track daily progress"]
    except Exception as e:
        print("Gemini API Error:", e)
        return ["Define goal milestone", "Execute step 1", "Track daily progress"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/goals", methods=["GET"])
@app.route("/api/goals", methods=["GET"])
def get_goals():
    if not SUPABASE_URL.startswith("http"):
        return jsonify([]), 200
    url = f"{SUPABASE_URL}/rest/v1/goals?select=*"
    r = requests.get(url, headers=headers)
    return jsonify(r.json()), r.status_code

@app.route("/goals", methods=["POST"])
@app.route("/api/goals", methods=["POST"])
def add_goal():
    data = request.json or {}
    goal_title = data.get("title", "")
    
    ai_roadmap = generate_roadmap_with_gemini(goal_title)
    if ai_roadmap:
        data["roadmap"] = ai_roadmap
        
    if not SUPABASE_URL.startswith("http"):
        return jsonify(data), 201

    url = f"{SUPABASE_URL}/rest/v1/goals"
    r = requests.post(url, headers=headers, json=data)
    return jsonify(r.json()), r.status_code

@app.route("/goals/<int:goal_id>", methods=["PATCH"])
@app.route("/api/goals/<int:goal_id>", methods=["PATCH"])
def update_goal(goal_id):
    if not SUPABASE_URL.startswith("http"):
        return jsonify({"message": "Updated"}), 200
    url = f"{SUPABASE_URL}/rest/v1/goals?id=eq.{goal_id}"
    data = request.json
    r = requests.patch(url, headers=headers, json=data)
    return jsonify(r.json()), r.status_code

@app.route("/goals/<int:goal_id>", methods=["DELETE"])
@app.route("/api/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    if not SUPABASE_URL.startswith("http"):
        return jsonify({"message": "Deleted"}), 200
    url = f"{SUPABASE_URL}/rest/v1/goals?id=eq.{goal_id}"
    r = requests.delete(url, headers=headers)
    return jsonify(r.json()), r.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

@app.route('/api/roadmap', methods=['POST'])
def generate_roadmap():
    data = request.get_json()
    goal = data.get('goal', 'Your Goal')
    
    steps = [
        f"Phase 1: Define core objectives and set daily target milestones for '{goal}'.",
        f"Phase 2: Complete practical foundational tasks systematically.",
        f"Phase 3: Work on small execution projects & test progress daily.",
        f"Phase 4: Review final outcomes, optimize performance and achieve consistency."
    ]
    return jsonify({"status": "success", "goal": goal, "steps": steps})
