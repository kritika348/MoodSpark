from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# =====================================
# OLLAMA CLOUD
# =====================================

OLLAMA_URL = "https://ollama.com/api/chat"

# Cloud model
MODEL = "gpt-oss:120b"

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Store previous challenges
previous_challenges = []


# =====================================
# ASK OLLAMA
# =====================================

def ask_ollama(prompt):

    if not OLLAMA_API_KEY:
        raise Exception("OLLAMA_API_KEY is missing in Render.")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        headers={
            "Authorization": "Bearer " + OLLAMA_API_KEY,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=120
    )

    print("Ollama status:", response.status_code)
    print("Ollama response:", response.text)

    response.raise_for_status()

    result = response.json()

    return result["message"]["content"]


# =====================================
# HOME
# =====================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================
# GENERATE CHALLENGE
# =====================================

@app.route("/generate", methods=["POST"])
def generate():

    data = request.get_json()
    mood = data.get("mood", "")

    previous = "\n".join(previous_challenges[-10:])

    prompt = f"""
You are MoodSpark, a fun creative challenge generator.

The user's mood is: {mood}

Create ONE tiny creative challenge.

RULES:

- Use very simple English.
- Maximum 2 short sentences.
- It must take only 2-5 minutes.
- Make it fun and interesting.
- Make the user want to try it.
- Do NOT give motivational advice.
- Do NOT give therapy advice.
- Do NOT give exercise challenges.
- Do NOT make it boring.
- Make every challenge different.
- Do not repeat previous challenges.

You can create challenges like:

DRAWING:
Draw a tiny monster using only circles.

CRAFT:
Make a paper butterfly using one small piece of paper.

PHOTO:
Take a funny photo of something that looks like a face.

WRITING:
Write a 3-line funny story about your shoe.

BRAIN:
Find 5 things around you that start with S.

IMAGINATION:
Invent a new ice cream flavour and give it a funny name.

OBSERVATION:
Find the smallest object near you and describe it.

Return ONLY:

TYPE: drawing / craft / photo / writing / brain / creative

CHALLENGE: one short challenge

TIME: 2-5 minutes

Previous challenges:
{previous}
"""

    try:

        challenge = ask_ollama(prompt)

        previous_challenges.append(challenge)

        return jsonify({
            "challenge": challenge
        })

    except Exception as e:

        print("OLLAMA GENERATE ERROR:", str(e))

        return jsonify({
            "error": str(e)
        }), 500


# =====================================
# SUBMIT CHALLENGE
# =====================================

@app.route("/submit", methods=["POST"])
def submit():

    data = request.get_json()

    mood = data.get("mood", "")
    challenge = data.get("challenge", "")
    submission = data.get("submission", "")

    prompt = f"""
You are the friendly judge of MoodSpark.

User mood:
{mood}

Challenge:
{challenge}

User's answer:
{submission}

Give friendly feedback.

Rules:

- Give a score from 1 to 10.
- Be positive.
- Mention something specific about their answer.
- Do not be harsh.
- Maximum 2 short sentences.

Return exactly:

SCORE: X/10

COMMENT: Your short friendly comment.
"""

    try:

        feedback = ask_ollama(prompt)

        score = "10/10"
        comment = feedback

        for line in feedback.splitlines():

            if line.upper().startswith("SCORE:"):
                score = line.split(":", 1)[1].strip()

            if line.upper().startswith("COMMENT:"):
                comment = line.split(":", 1)[1].strip()

        return jsonify({
            "score": score,
            "feedback": comment
        })

    except Exception as e:

        print("OLLAMA SUBMIT ERROR:", str(e))

        return jsonify({
            "error": str(e)
        }), 500


# =====================================
# START SERVER
# =====================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )