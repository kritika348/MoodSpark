from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# ==========================================
# OLLAMA CLOUD SETTINGS
# ==========================================

OLLAMA_URL = "https://ollama.com/api/chat"
MODEL = "gemma3:4b"

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

previous_challenges = []


# ==========================================
# OLLAMA API
# ==========================================

def ask_ollama(prompt, image_base64=None):

    if not OLLAMA_API_KEY:
        raise Exception("OLLAMA_API_KEY is not set on Render.")

    message = {
        "role": "user",
        "content": prompt
    }

    # Add image for drawing/photo submissions
    if image_base64:

        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        message["images"] = [image_base64]

    payload = {
        "model": MODEL,
        "messages": [message],
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=180
    )

    response.raise_for_status()

    result = response.json()

    return result["message"]["content"]


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# GENERATE CHALLENGE
# ==========================================

@app.route("/generate", methods=["POST"])
def generate():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No data received."
            }), 400

        mood = data.get("mood", "").strip()

        if not mood:
            return jsonify({
                "error": "Please select a mood."
            }), 400

        previous = "\n".join(
            previous_challenges[-10:]
        )

        prompt = f"""
You are MoodSpark, a fun creative challenge AI.

User mood: {mood}

Create ONE tiny creative challenge.

RULES:

1. Use VERY SIMPLE English.
2. Keep the challenge SHORT.
3. Maximum 1 or 2 sentences.
4. It must take only 2-5 minutes.
5. Make it fun, playful and creative.
6. Make the user WANT to do it.
7. Do not give motivational advice.
8. Do not give therapy advice.
9. Do not give exercise challenges.
10. Give only ONE challenge.
11. Do not repeat previous challenges.

Choose ONE type:

drawing
craft
photo
writing
puzzle
brain
creative

Examples:

TYPE: drawing
CHALLENGE: Draw a tiny monster using only circles and triangles.
TIME: 3 minutes

TYPE: craft
CHALLENGE: Make a tiny paper animal using one sheet of paper.
TIME: 5 minutes

TYPE: photo
CHALLENGE: Find something around you that looks like a face and take a photo.
TIME: 3 minutes

TYPE: writing
CHALLENGE: Write a funny 3-line story about your shoe.
TIME: 3 minutes

TYPE: puzzle
CHALLENGE: Find 5 things around you that start with S.
TIME: 3 minutes

Previous challenges:
{previous}

Return ONLY this format:

TYPE: drawing/craft/photo/writing/puzzle/brain/creative
CHALLENGE: short challenge
TIME: 2-5 minutes
"""

        challenge = ask_ollama(prompt)

        previous_challenges.append(challenge)

        return jsonify({
            "challenge": challenge
        })

    except Exception as e:

        print("OLLAMA GENERATE ERROR:", str(e))

        return jsonify({
            "error": "Could not create challenge.",
            "details": str(e)
        }), 500


# ==========================================
# SUBMIT CHALLENGE
# ==========================================

@app.route("/submit", methods=["POST"])
def submit():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No submission data received."
            }), 400

        mood = data.get("mood", "")
        challenge = data.get("challenge", "")
        submission = data.get("submission", "")
        submission_type = data.get(
            "submission_type",
            "text"
        )

        if not submission:
            return jsonify({
                "error": "Please complete the challenge first."
            }), 400

        # ======================================
        # DRAWING / IMAGE SUBMISSION
        # ======================================

        if submission_type in ["drawing", "image"]:

            feedback_prompt = f"""
You are the friendly judge of MoodSpark.

User mood:
{mood}

Challenge:
{challenge}

The user submitted an image of their completed challenge.

Look carefully at the image.

Judge the submission based on:

- Effort
- Creativity
- How well it matches the challenge
- Overall idea

Give a genuine score from 1 to 10.

Do NOT automatically give 10/10.

Mention something specific you noticed in the image.

Be positive, friendly and impressive.

Maximum 2 sentences.

Return ONLY:

SCORE: X/10

COMMENT:
Your personalized comment.
"""

            feedback = ask_ollama(
                feedback_prompt,
                image_base64=submission
            )

        # ======================================
        # TEXT SUBMISSION
        # ======================================

        else:

            feedback_prompt = f"""
You are the friendly judge of MoodSpark.

User mood:
{mood}

Challenge:
{challenge}

User's answer:
{submission}

Judge the answer based on:

- Effort
- Creativity
- How well it completes the challenge

Give a genuine score from 1 to 10.

Do NOT automatically give 10/10.

Mention something specific about the user's answer.

Be positive, friendly and impressive.

Maximum 2 sentences.

Return ONLY:

SCORE: X/10

COMMENT:
Your personalized comment.
"""

            feedback = ask_ollama(
                feedback_prompt
            )

        # ======================================
        # EXTRACT SCORE
        # ======================================

        score = "10/10"

        for line in feedback.splitlines():

            if "SCORE:" in line.upper():

                score = line.split(
                    ":",
                    1
                )[1].strip()

                break

        # ======================================
        # EXTRACT COMMENT
        # ======================================

        comment = feedback

        if "COMMENT:" in feedback:

            comment = feedback.split(
                "COMMENT:",
                1
            )[1].strip()

        return jsonify({
            "score": score,
            "feedback": comment
        })

    except Exception as e:

        print("OLLAMA SUBMIT ERROR:", str(e))

        return jsonify({
            "error": "Could not evaluate submission.",
            "details": str(e)
        }), 500


# ==========================================
# START SERVER
# ==========================================

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