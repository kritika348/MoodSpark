from flask import Flask, render_template, request, jsonify
import requests
import os
import base64

app = Flask(__name__)

# =========================
# OLLAMA CLOUD
# =========================

OLLAMA_URL = "https://ollama.com/api/chat"

# Vision model: supports text + images
MODEL = "gemma3:4b"

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

previous_challenges = []


# =========================
# OLLAMA TEXT REQUEST
# =========================

def ask_ollama(prompt, image_base64=None):

    if not OLLAMA_API_KEY:
        raise Exception("OLLAMA_API_KEY is not configured.")

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    # Send image when available
    if image_base64:
        # Remove data:image/png;base64, or similar prefix
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        payload["images"] = [image_base64]

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

    return response.json()["response"]


# =========================
# HOME
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
    mood = data.get("mood", "")

    previous = "\n".join(previous_challenges[-10:])

    prompt = f"""
You are MoodSpark, a fun creative challenge AI.

User mood: {mood}

Create ONE fun mini challenge.

IMPORTANT:
- Use VERY SIMPLE English.
- Challenge must be SHORT.
- Maximum 1-2 sentences for the challenge.
- It must take 2-5 minutes.
- Make it playful, creative and interesting.
- Avoid boring motivational advice.
- Avoid exercise or therapy advice.
- Make the user WANT to actually do it.
- Give a different challenge every time.
- Do not repeat previous challenges.

Use one of these types:

drawing
craft
photo
writing
puzzle
brain
creative

Examples of GOOD challenges:

TYPE: drawing
CHALLENGE: Draw a tiny monster using only circles and triangles.

TYPE: craft
CHALLENGE: Make a tiny paper animal using one sheet of paper.

TYPE: photo
CHALLENGE: Find something around you that looks like a face and take a photo.

TYPE: writing
CHALLENGE: Write a funny 3-line story about your shoe.

TYPE: puzzle
CHALLENGE: Find 5 things around you that start with the letter S.

Previous challenges:
{previous}

Return ONLY this format:

TYPE: drawing/craft/photo/writing/puzzle/brain/creative

CHALLENGE: short challenge

TIME: 2-5 minutes
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
            "error": str(e)
        }), 500


# =========================
# SUBMIT + AI EVALUATION
# =========================

@app.route("/submit", methods=["POST"])
def submit():

    data = request.json

    mood = data.get("mood", "")
    challenge = data.get("challenge", "")
    submission = data.get("submission", "")
    submission_type = data.get("submission_type", "text")

    image_base64 = None

    if submission_type in ["drawing", "image"]:
        image_base64 = submission

    # =========================
    # IMAGE EVALUATION
    # =========================

    if image_base64:

        feedback_prompt = f"""
You are the friendly judge of MoodSpark.

User mood:
{mood}

Challenge:
{challenge}

The user submitted an image of their completed challenge.

Look carefully at the image.

Judge the submission based on:
- Did they attempt the challenge?
- Creativity
- Effort
- How well it matches the challenge

Be encouraging, especially for simple or beginner work.

Give a score from 1 to 10.

IMPORTANT:
- Do NOT give everyone 10/10 automatically.
- Do not be harsh.
- Give a genuine score.
- Mention something specific you noticed.
- Keep the comment impressive and positive.
- Maximum 2 sentences.

Return ONLY:

SCORE: X/10

COMMENT:
Your short personalized comment.
"""

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

Give a score from 1 to 10.

IMPORTANT:
- Do NOT give everyone 10/10 automatically.
- Be positive but genuine.
- Give a specific and impressive comment.
- Maximum 2 sentences.

Return ONLY:

SCORE: X/10

COMMENT:
Your short personalized comment.
"""

    try:

        feedback = ask_ollama(
            feedback_prompt,
            image_base64=image_base64
        )

        # Try to extract score
        score = "10/10"

        for line in feedback.splitlines():
            if "SCORE:" in line.upper():
                score = line.split(":", 1)[1].strip()
                break

        comment = feedback

        if "COMMENT:" in feedback:
            comment = feedback.split("COMMENT:", 1)[1].strip()

        return jsonify({
            "score": score,
            "feedback": comment
        })

    except Exception as e:

        print("Ollama Evaluation Error:", str(e))

        return jsonify({
            "error": str(e)
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