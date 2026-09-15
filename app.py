from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json"
}

GOALS_URL = SUPABASE_URL.rstrip("/") + "/goals"


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "backend": "Flask",
        "database": "Supabase"
    })


@app.route("/goals", methods=["GET"])
def get_goals():
    response = requests.get(
        GOALS_URL,
        headers=HEADERS,
        params={"select": "*", "order": "created_at.desc"},
        timeout=15
    )

    return jsonify(response.json()), response.status_code


@app.route("/goals", methods=["POST"])
def add_goal():
    data = request.get_json(silent=True)

    if not data or not data.get("goal"):
        return jsonify({
            "error": "Goal text missing!"
        }), 400

    payload = {
        "goal": data["goal"],
        "target_date": data.get("target_date"),
        "category": data.get("category"),
        "progress": data.get("progress", 0)
    }

    response = requests.post(
        GOALS_URL,
        headers={
            **HEADERS,
            "Prefer": "return=representation"
        },
        json=payload,
        timeout=15
    )

    return jsonify(response.json()), response.status_code


@app.route("/goals/<int:goal_id>", methods=["PATCH"])
def update_goal(goal_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "No data provided!"
        }), 400

    allowed_fields = {
        "goal",
        "target_date",
        "category",
        "progress"
    }

    payload = {
        key: data[key]
        for key in allowed_fields
        if key in data
    }

    if not payload:
        return jsonify({
            "error": "No valid fields provided!"
        }), 400

    response = requests.patch(
        GOALS_URL,
        headers={
            **HEADERS,
            "Prefer": "return=representation"
        },
        params={"id": f"eq.{goal_id}"},
        json=payload,
        timeout=15
    )

    return jsonify(response.json()), response.status_code


@app.route("/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    response = requests.delete(
        GOALS_URL,
        headers={
            **HEADERS,
            "Prefer": "return=representation"
        },
        params={"id": f"eq.{goal_id}"},
        timeout=15
    )

    return jsonify(response.json()), response.status_code


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(
        host="0.0.0.0",
        port=port
    )
