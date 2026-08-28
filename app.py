from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# =========================================================
# OLLAMA CLOUD SETTINGS
# =========================================================

OLLAMA_URL = "https://ollama.com/api/chat"
MODEL = "gpt-oss:120b"

OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

# Store recent challenges so AI tries not to repeat them
previous_challenges = []


# =========================================================
# OLLAMA AI FUNCTION
# =========================================================

def ask_ollama(prompt):

    if not OLLAMA_API_KEY:
        raise Exception(
            "OLLAMA_API_KEY is missing. "
            "Add it in Render Environment Variables."
        )

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
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
        headers=headers,
        json=data,
        timeout=120
    )

    print("OLLAMA STATUS:", response.status_code)
    print("OLLAMA RESPONSE:", response.text)

    response.raise_for_status()

    result = response.json()

    # Ollama Cloud chat response
    return result["message"]["content"]


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# GENERATE CREATIVE CHALLENGE
# =========================================================

@app.route("/generate", methods=["POST"])
def generate():

    try:

        data = request.get_json(silent=True) or {}

        mood = data.get("mood", "happy")

        previous = "\n".join(
            previous_challenges[-10:]
        )

        prompt = f"""
You are MoodSpark, a fun and creative AI challenge generator.

The user's current mood is:
{mood}

Create ONE short and interesting mini challenge.

IMPORTANT RULES:

1. Use very simple English.
2. The challenge must take only 2-5 minutes.
3. Make it playful, creative and fun.
4. Make the user WANT to do it.
5. Do not give boring motivational advice.
6. Do not give therapy advice.
7. Do not suggest exercise.
8. Do not repeat previous challenges.
9. Drawing challenges are allowed.
10. Writing challenges are allowed.
11. Puzzle challenges are allowed.
12. Craft challenges are allowed.
13. Brain challenges are allowed.
14. The challenge should be possible with normal things around the user.

Possible challenge types:

drawing
craft
writing
puzzle
brain
creative

Examples:

TYPE: drawing
CHALLENGE: Draw a funny cartoon monster using only circles and triangles.
TIME: 2-5 minutes

TYPE: writing
CHALLENGE: Write a funny 3-line story about your shoe.
TIME: 2-5 minutes

TYPE: puzzle
CHALLENGE: Find 5 things around you that start with the letter S.
TIME: 2-5 minutes

TYPE: creative
CHALLENGE: Invent a completely useless but funny invention.
TIME: 2-5 minutes

Previous challenges:
{previous}

Return ONLY this format:

TYPE: drawing/craft/writing/puzzle/brain/creative

CHALLENGE: your short challenge

TIME: 2-5 minutes
"""

        challenge = ask_ollama(prompt)

        previous_challenges.append(challenge)

        # Keep only recent challenges
        if len(previous_challenges) > 20:
            previous_challenges.pop(0)

        return jsonify({
            "success": True,
            "challenge": challenge
        })

    except Exception as e:

        print("OLLAMA GENERATE ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# SUBMIT CHALLENGE + AI EVALUATION
# =========================================================

@app.route("/submit", methods=["POST"])
def submit():

    try:

        data = request.get_json(silent=True) or {}

        mood = data.get("mood", "")
        challenge = data.get("challenge", "")
        submission = data.get("submission", "")
        submission_type = data.get(
            "submission_type",
            "text"
        )

        if not submission:

            return jsonify({
                "success": False,
                "error": "Please submit your challenge first."
            }), 400


        prompt = f"""
You are the friendly AI judge of MoodSpark.

USER MOOD:
{mood}

CHALLENGE:
{challenge}

USER SUBMISSION:
{submission}

SUBMISSION TYPE:
{submission_type}

Evaluate the user's submission.

Consider:

- Effort
- Creativity
- How well the challenge was completed
- Originality

Give a genuine score from 1 to 10.

IMPORTANT:

- Do not automatically give 10/10.
- Do not be unnecessarily harsh.
- Be encouraging.
- Mention something specific about the submission.
- Keep the feedback short.
- Maximum 2 sentences.

Return ONLY this format:

SCORE: X/10

COMMENT: Your short personalized comment.
"""

        feedback = ask_ollama(prompt)

        score = "8/10"
        comment = feedback

        # Extract score and comment
        for line in feedback.splitlines():

            line_clean = line.strip()

            if line_clean.upper().startswith("SCORE:"):

                score = line_clean.split(
                    ":",
                    1
                )[1].strip()

            elif line_clean.upper().startswith("COMMENT:"):

                comment = line_clean.split(
                    ":",
                    1
                )[1].strip()


        return jsonify({
            "success": True,
            "score": score,
            "feedback": comment
        })

    except Exception as e:

        print(
            "OLLAMA EVALUATION ERROR:",
            str(e)
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "model": MODEL,
        "message": "MoodSpark AI is running!"
    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )