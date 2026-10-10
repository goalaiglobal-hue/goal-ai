import os
import re
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')

@app.route('/')
def index():
    return render_template('index.html')

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
                'model': 'google/gemini-2.0-flash-lite-001',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.7
            }
            
            response = requests.post('https://openrouter.ai/api/v1/chat/completions', json=payload, headers=headers, timeout=10)
            
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
        print('AI Generation Exception:', e)

    fallback_steps = [
        f'Phase 1: Define core objectives and set daily target milestones for {goal}.',
        'Phase 2: Complete practical foundational tasks systematically.',
        'Phase 3: Work on small execution projects & test progress daily.',
        'Phase 4: Review final outcomes, optimize performance and achieve consistency.'
    ]
    return jsonify({'steps': fallback_steps})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
