import os
import re
import requests
from flask import Flask, render_template, request, jsonify, make_response, session, redirect

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'goalai-secret-key-2026')

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

def get_supabase_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    rendered = render_template('index.html', user_email=session.get('user_email', ''))
    response = make_response(rendered)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({'error': 'Email and Password are required'}), 400
        
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({'error': 'Database not configured'}), 500
        
    try:
        res = requests.get(f'{SUPABASE_URL}/rest/v1/app_users?email=eq.{email}', headers=get_supabase_headers(), timeout=10)
        if res.status_code == 200 and len(res.json()) > 0:
            return jsonify({'error': 'Email already registered! Please login.'}), 400
            
        payload = {'email': email, 'password': password}
        res_create = requests.post(f'{SUPABASE_URL}/rest/v1/app_users', headers=get_supabase_headers(), json=payload, timeout=10)
        
        if res_create.status_code in [200, 201]:
            user = res_create.json()[0]
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            return jsonify({'status': 'success', 'message': 'Account created successfully!'})
        else:
            return jsonify({'error': 'Failed to create account'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({'error': 'Email and Password are required'}), 400
        
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({'error': 'Database not configured'}), 500
        
    try:
        res = requests.get(f'{SUPABASE_URL}/rest/v1/app_users?email=eq.{email}&password=eq.{password}', headers=get_supabase_headers(), timeout=10)
        if res.status_code == 200:
            users = res.json()
            if users:
                user = users[0]
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                return jsonify({'status': 'success', 'message': 'Logged in successfully!'})
            else:
                return jsonify({'error': 'Invalid Email or Password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    return jsonify({'error': 'Login failed'}), 400

@app.route('/api/data', methods=['GET'])
def get_data():
    user_id = session.get('user_id')
    if not user_id or not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({'goal': '', 'tasks': []})
    
    try:
        res = requests.get(f'{SUPABASE_URL}/rest/v1/user_goals?user_id=eq.{user_id}', headers=get_supabase_headers(), timeout=10)
        if res.status_code == 200:
            rows = res.json()
            if rows:
                return jsonify({'goal': rows[0].get('goal', ''), 'tasks': rows[0].get('tasks', [])})
    except Exception as e:
        print('Fetch Error:', e)
        
    return jsonify({'goal': '', 'tasks': []})

@app.route('/api/data', methods=['POST'])
def save_data():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    goal = data.get('goal', '')
    tasks = data.get('tasks', [])
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({'status': 'success'})
        
    try:
        payload = {'id': user_id, 'user_id': user_id, 'goal': goal, 'tasks': tasks}
        res = requests.post(
            f'{SUPABASE_URL}/rest/v1/user_goals',
            headers={**get_supabase_headers(), 'Prefer': 'resolution=merge-duplicates'},
            json=payload,
            timeout=10
        )
        if res.status_code in [200, 201]:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': res.text}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/roadmap', methods=['POST'])
def generate_roadmap():
    data = request.get_json() or {}
    goal = data.get('goal', '').strip()
    
    if not goal:
        return jsonify({'error': 'Goal is required'}), 400
        
    try:
        if OPENROUTER_API_KEY:
            headers = {
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://goal-ai-dw76.onrender.com',
                'X-Title': 'Goal AI'
            }
            
            prompt = f"You are Goal AI, an elite productivity assistant. Generate a crisp, highly actionable 4-phase execution roadmap for the following goal: '{goal}'. Provide exactly 4 phases. Keep each phase clear, impactful, and direct under 20 words per phase. Format your response EXACTLY as 4 lines, starting with Phase 1:, Phase 2:, Phase 3:, Phase 4:"

            payload = {
                'model': 'meta-llama/llama-3.3-70b-instruct:free',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.7
            }
            
            response = requests.post('https://openrouter.ai/api/v1/chat/completions', json=payload, headers=headers, timeout=12)
            
            if response.status_code == 200:
                ai_data = response.json()
                content = ai_data['choices'][0]['message']['content'].strip()
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                
                steps = []
                for line in lines:
                    clean_line = re.sub(r'^(Phase\s*\d+:?\s*|\d+\.\s*|-\s*)', '', line, flags=re.IGNORECASE).strip()
                    if clean_line:
                        steps.append(clean_line)
                
                if len(steps) >= 4:
                    return jsonify({'steps': steps[:4]})
    except Exception as e:
        print('AI Exception:', e)

    fallback_steps = [
        f'Phase 1: Define core objectives and set daily target milestones for {goal}.',
        'Phase 2: Complete practical foundational tasks systematically.',
        'Phase 3: Work on small execution projects & test progress daily.',
        'Phase 4: Review final outcomes, optimize performance and achieve consistency.'
    ]
    return jsonify({'steps': fallback_steps})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
