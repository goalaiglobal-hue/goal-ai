from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip('/')
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/goals", methods=["GET"])
def get_goals():
    url = f"{SUPABASE_URL}/rest/v1/goals?select=*"
    r = requests.get(url, headers=headers)
    return jsonify(r.json()), r.status_code

@app.route("/goals/<int:goal_id>", methods=["PATCH"])
def update_goal(goal_id):
    url = f"{SUPABASE_URL}/rest/v1/goals?id=eq.{goal_id}"
    data = request.json
    r = requests.patch(url, headers=headers, json=data)
    return jsonify(r.json()), r.status_code

@app.route("/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    url = f"{SUPABASE_URL}/rest/v1/goals?id=eq.{goal_id}"
    r = requests.delete(url, headers=headers)
    return jsonify(r.json()), r.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
