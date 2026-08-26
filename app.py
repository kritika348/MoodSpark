from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

# Store challenges during the current session
previous_challenges = []


def ask_ollama(prompt):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    response.raise_for_status()

    return response.json()["response"]


@app.route("/")
def home():
    return render_template("index.html")


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

    challenge = ask_ollama(prompt)

    previous_challenges.append(challenge)

    return jsonify({
        "challenge": challenge
    })


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

    feedback = ask_ollama(feedback_prompt)

    return jsonify({
        "feedback": feedback
    })


if __name__ == "__main__":
    app.run(debug=True)