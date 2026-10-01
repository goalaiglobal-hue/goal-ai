from flask import Flask, jsonify, request, render_template
import os
import requests

app = Flask(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

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
    r = requests.get(
        SUPABASE_URL + "goals?select=*",
        headers=headers
    )
    return jsonify(r.json()), r.status_code

@app.route("/goals", methods=["POST"])
def add_goal():
    data = request.get_json()
    if not data or not data.get("goal"):
        return jsonify({"error": "Goal text missing!"}), 400

    payload = {
        "goal": data["goal"],
        "target_date": data.get("target_date"),
        "category": data.get("category"),
        "progress": data.get("progress", 0)
    }

    r = requests.post(
        SUPABASE_URL + "goals",
        headers={
            **headers,
            "Prefer": "return=representation"
        },
        json=payload
    )
    return jsonify(r.json()), r.status_code

@app.route("/goals/<int:goal_id>", methods=["PATCH"])
def update_goal(goal_id):
    data = request.get_json()
    r = requests.patch(
        SUPABASE_URL + f"goals?id=eq.{goal_id}",
        headers={
            **headers,
            "Prefer": "return=representation"
        },
        json=data
    )
    return jsonify(r.json()), r.status_code

@app.route("/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    r = requests.delete(
        SUPABASE_URL + f"goals?id=eq.{goal_id}",
        headers=headers
    )
    return jsonify({"message": "Goal deleted", "status": r.status_code}), r.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
