from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# =========================
# OLLAMA CLOUD SETTINGS
# =========================

OLLAMA_URL = "https://ollama.com/api/generate"
MODEL = "llama3.2"

# API key Render Environment Variable se aayegi
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Store challenges during current session
previous_challenges = []


# =========================
# OLLAMA AI FUNCTION
# =========================

def ask_ollama(prompt):

    if not OLLAMA_API_KEY:
        raise Exception("OLLAMA_API_KEY is not configured on Render.")

    response = requests.post(
        OLLAMA_URL,
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    return result["response"]


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# GENERATE CHALLENGE
# =========================

@app.route("/generate", methods=["POST"])
def generate():

    data = request.json

    mood = data.get("mood")

    previous = "\n".join(previous_challenges)

    prompt = f"""
You are MoodMaker AI.

The user's mood is:
{mood}

Create ONE small creative challenge for the user.

The challenge should help the user shift their mood
in a positive and playful direction.

IMPORTANT RULES:

- The challenge must take only 2-5 minutes.
- Keep it short.
- Make it creative and interesting.
- Make it easy to do immediately.
- Match the user's mood.
- Give only ONE challenge.
- Do not give generic motivational advice.
- Do not give medical or therapy advice.
- Every challenge should be different.
- Do not repeat previous challenges.

Possible challenge types:

Drawing
Making something
Puzzle
Brain challenge
Writing
Storytelling
Photography
Observation
Music
Funny challenge
Imagination
Creative problem solving

Previous challenges:

{previous}

Generate a NEW challenge.

Return ONLY in this format:

TYPE: drawing / making / puzzle / writing / photo / other

CHALLENGE:
Short challenge here

TIME:
2-5 minutes

SUBMISSION:
image or text
"""

    try:
        challenge = ask_ollama(prompt)

        previous_challenges.append(challenge)

        return jsonify({
            "challenge": challenge
        })

    except Exception as e:

        print("Ollama Error:", str(e))

        return jsonify({
            "error": "Unable to connect to MoodSpark AI.",
            "details": str(e)
        }), 500


# =========================
# SUBMIT CHALLENGE
# =========================

@app.route("/submit", methods=["POST"])
def submit():

    data = request.json

    mood = data.get("mood")
    challenge = data.get("challenge")
    submission = data.get("submission")

    feedback_prompt = f"""
You are MoodMaker AI.

User mood:
{mood}

Challenge:
{challenge}

User's completed work/answer:
{submission}

Give a short, friendly and encouraging response.

Rules:
- Appreciate the user's effort.
- Keep it positive.
- Maximum 2 sentences.
- Do not judge harshly.
"""

    try:
        feedback = ask_ollama(feedback_prompt)

        return jsonify({
            "feedback": feedback
        })

    except Exception as e:

        print("Ollama Error:", str(e))

        return jsonify({
            "error": "Unable to connect to MoodSpark AI.",
            "details": str(e)
        }), 500


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )