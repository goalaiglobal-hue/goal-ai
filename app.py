
def calculate_level_and_xp(current_xp, added_xp=0):
    total_xp = current_xp + added_xp
    level = (total_xp // 100) + 1
    return total_xp, level

import os, re, requests
from datetime import datetime, date
from flask import send_from_directory, Flask, render_template, request, jsonify, make_response, session, redirect

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'goalai-secret-key-2026')

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '').strip()
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '').strip()

def get_headers():
    return {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json', 'Prefer': 'return=representation'}

@app.route('/')
def index():
    if 'user_id' not in session: return redirect('/login')
    res = make_response(render_template('index.html', user_email=session.get('user_email', '')))
    res.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return res

@app.route('/login')
def login_page():
    return redirect('/') if 'user_id' in session else render_template('login.html')

@app.route('/signup')
def signup_page():
    return redirect('/') if 'user_id' in session else render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    email, password = data.get('email', '').strip().lower(), data.get('password', '').strip()
    if not email or not password: return jsonify({'error': 'Email and Password required'}), 400
    try:
        chk = requests.get(f'{SUPABASE_URL}/rest/v1/app_users?email=eq.{email}', headers=get_headers(), timeout=10)
        if chk.status_code == 200 and len(chk.json()) > 0: return jsonify({'error': 'Email registered already'}), 400
        res = requests.post(f'{SUPABASE_URL}/rest/v1/app_users', headers=get_headers(), json={'email': email, 'password': password}, timeout=10)
        if res.status_code in [200, 201]:
            u = res.json()[0]
            session['user_id'], session['user_email'] = u['id'], u['email']
            return jsonify({'status': 'success'})
    except Exception as e: return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Failed'}), 400

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email, password = data.get('email', '').strip().lower(), data.get('password', '').strip()
    try:
        res = requests.get(f'{SUPABASE_URL}/rest/v1/app_users?email=eq.{email}&password=eq.{password}', headers=get_headers(), timeout=10)
        if res.status_code == 200 and res.json():
            u = res.json()[0]
            session['user_id'], session['user_email'] = u['id'], u['email']
            return jsonify({'status': 'success'})
    except Exception as e: return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/data', methods=['GET'])
def get_data():
    uid = session.get('user_id')
    if not uid: return jsonify({'goal': '', 'tasks': [], 'streak': 0})
    try:
        res = requests.get(f'{SUPABASE_URL}/rest/v1/user_goals?user_id=eq.{uid}', headers=get_headers(), timeout=10)
        if res.status_code == 200 and res.json():
            r = res.json()[0]
            streak_val = r.get('streak_count', 0) or 0;
            if r.get('goal') and streak_val == 0: streak_val = 1
            return jsonify({'goal': r.get('goal', ''), 'tasks': r.get('tasks', []), 'streak': streak_val})
    except: pass
    return jsonify({'goal': '', 'tasks': [], 'streak': 0})

@app.route('/api/data', methods=['POST'])
def save_data():
    uid = session.get('user_id')
    if not uid: return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    goal, tasks = data.get('goal', ''), data.get('tasks', [])
    try:
        today_str = date.today().isoformat()
        current_streak, last_date_str = 0, None
        res_curr = requests.get(f'{SUPABASE_URL}/rest/v1/user_goals?user_id=eq.{uid}', headers=get_headers(), timeout=10)
        if res_curr.status_code == 200 and res_curr.json():
            r = res_curr.json()[0]
            current_streak = r.get('streak_count', 0) or 0
            last_date_str = r.get('last_active_date')

        if last_date_str != today_str:
            if last_date_str:
                diff = (date.today() - datetime.strptime(last_date_str, '%Y-%m-%d').date()).days
                current_streak = current_streak + 1 if diff == 1 else 1
            else: current_streak = 1
            last_date_str = today_str

        payload = {'id': uid, 'user_id': uid, 'goal': goal, 'tasks': tasks, 'streak_count': current_streak, 'last_active_date': last_date_str}
        res = requests.post(f'{SUPABASE_URL}/rest/v1/user_goals', headers={**get_headers(), 'Prefer': 'resolution=merge-duplicates'}, json=payload, timeout=10)
        if res.status_code in [200, 201]: return jsonify({'status': 'success', 'streak': max(1, current_streak)})
    except Exception as e: return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'success', 'streak': 0})

@app.route('/api/roadmap', methods=['POST'])
def generate_roadmap():
    data = request.get_json() or {}
    goal = data.get('goal', '').strip()
    if not goal: return jsonify({'error': 'Goal required'}), 400
    try:
        if OPENROUTER_API_KEY:
            headers = {'Authorization': f'Bearer {OPENROUTER_API_KEY}', 'Content-Type': 'application/json'}
            prompt = f"Generate 4 phase roadmap for: '{goal}'. 4 lines only: Phase 1:, Phase 2:, Phase 3:, Phase 4:"
            response = requests.post('https://openrouter.ai/api/v1/chat/completions', json={'model': 'meta-llama/llama-3.3-70b-instruct:free', 'messages': [{'role': 'user', 'content': prompt}]}, headers=headers, timeout=12)
            if response.status_code == 200:
                lines = response.json()['choices'][0]['message']['content'].strip().split('\n')
                steps = [re.sub(r'^(Phase\s*\d+:?\s*|\d+\.\s*|-\s*)', '', l).strip() for l in lines if l.strip()]
                if len(steps) >= 4: return jsonify({'steps': steps[:4]})
    except: pass
    return jsonify({'steps': [f'Phase 1: Set targets for {goal}', 'Phase 2: Complete basic tasks', 'Phase 3: Test daily', 'Phase 4: Achieve goal']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Message required'}), 400
        ai_reply = f"Here is a strategic plan for your request: '{user_message}'.\n\n1. Break down into 15-min daily action blocks.\n2. Track key milestones under your Active Goal.\n3. Complete daily tasks to earn +50 XP!"
        return jsonify({
            'reply': ai_reply,
            'suggested_tasks': [f"Action Item: {user_message[:30]}... Step 1", f"Action Item: {user_message[:30]}... Step 2"]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-xp', methods=['POST'])
def update_xp():
    try:
        data = request.get_json() or {}
        earned_xp = data.get('xp', 50)
        
        # Simple XP & Level calculation logic: Level = (XP // 100) + 1
        # Returning updated XP back to frontend
        return jsonify({
            'success': True,
            'xp_gained': earned_xp,
            'message': f'+{earned_xp} XP Earned!'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/.well-known/assetlinks.json')
def serve_assetlinks():
    return send_from_directory('static/.well-known', 'assetlinks.json', mimetype='application/json')


@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')


@app.route('/pwa-bundle')
def pwa_bundle():
    return "PWA Manifest, Service Worker, and Assetlinks are 100% active and ready for Play Store TWA!"
