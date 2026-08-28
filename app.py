from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# ==================================================
# OLLAMA SETTINGS
# ==================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

previous_challenges = []


# ==================================================
# ASK OLLAMA
# ==================================================

def ask_ollama(prompt, image_base64=None):

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    # Drawing image
    if image_base64:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        payload["images"] = [image_base64]

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=180
    )

    response.raise_for_status()

    result = response.json()

    return result.get("response", "")


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():
    return render_template("index.html")


# ==================================================
# GENERATE CHALLENGE
# ==================================================

@app.route("/generate", methods=["POST"])
def generate():

    try:

        data = request.get_json()
        mood = data.get("mood", "")

        previous = "\n".join(previous_challenges[-10:])

        prompt = f"""
You are MoodSpark, a fun creative challenge generator.

User mood: {mood}

Create ONE short and fun challenge.

RULES:

- Use very simple English.
- Maximum 1 or 2 short sentences.
- Challenge should take 2-5 minutes.
- Make it creative and playful.
- Do NOT give boring motivational advice.
- Give something people actually want to try.
- Do not repeat previous challenges.

You can create these types:

drawing
craft
photo
writing
puzzle
brain
creative

IMPORTANT:
If the challenge requires drawing, use TYPE: drawing.

Examples:

TYPE: drawing
CHALLENGE: Draw a funny cartoon cat wearing sunglasses.

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

Return ONLY:

TYPE: drawing/craft/photo/writing/puzzle/brain/creative

CHALLENGE: your short challenge

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
            "error": str(e)
        }), 500


# ==================================================
# SUBMIT + AI EVALUATION
# ==================================================

@app.route("/submit", methods=["POST"])
def submit():

    try:

        data = request.get_json()

        mood = data.get("mood", "")
        challenge = data.get("challenge", "")
        submission = data.get("submission", "")
        submission_type = data.get("submission_type", "text")

        # ------------------------------------------
        # DRAWING
        # ------------------------------------------

        if submission_type == "drawing":

            feedback_prompt = f"""
You are the friendly judge of MoodSpark.

User mood:
{mood}

Challenge:
{challenge}

The user completed the challenge by drawing on a canvas.

Look carefully at the drawing.

Evaluate:

1. Did the user attempt the challenge?
2. Creativity
3. Effort
4. How well it matches the challenge

Give a genuine score from 1 to 10.

Be encouraging but honest.

Mention something SPECIFIC you noticed in the drawing.

Keep the comment short and impressive.

Return ONLY:

SCORE: X/10
COMMENT: Your personalized comment.
"""

            feedback = ask_ollama(
                feedback_prompt,
                image_base64=submission
            )

        # ------------------------------------------
        # TEXT
        # ------------------------------------------

        else:

            feedback_prompt = f"""
You are the friendly judge of MoodSpark.

User mood:
{mood}

Challenge:
{challenge}

User submission:
{submission}

Evaluate:

1. Effort
2. Creativity
3. How well the challenge was completed

Give a genuine score from 1 to 10.

Be positive but honest.

Mention something specific about the submission.

Keep the comment short and impressive.

Return ONLY:

SCORE: X/10
COMMENT: Your personalized comment.
"""

            feedback = ask_ollama(feedback_prompt)

        # ------------------------------------------
        # EXTRACT SCORE
        # ------------------------------------------

        score = "8/10"

        for line in feedback.splitlines():

            if "SCORE:" in line.upper():

                score = line.split(":", 1)[1].strip()

                break

        # ------------------------------------------
        # EXTRACT COMMENT
        # ------------------------------------------

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

        print("OLLAMA EVALUATION ERROR:", str(e))

        return jsonify({

            "error": str(e)

        }), 500


# ==================================================
# START SERVER
# ==================================================

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