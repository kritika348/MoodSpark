from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# =====================================
# OLLAMA CLOUD SETTINGS
# =====================================

OLLAMA_URL = "https://ollama.com/api/chat"
MODEL = "gemma3:4b"

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Store previous challenges
previous_challenges = []


# =====================================
# OLLAMA API FUNCTION
# =====================================

def ask_ollama(prompt, image_base64=None):

    if not OLLAMA_API_KEY:
        raise Exception("OLLAMA_API_KEY is not configured on Render.")

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    # Add image if submitted
    if image_base64:

        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        messages[0]["images"] = [image_base64]

    payload = {
        "model": MODEL,
        "messages": messages,
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

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No data received."
            }), 400

        mood = data.get("mood", "")

        if not mood:
            return jsonify({
                "error": "Please select a mood."
            }), 400

        previous = "\n".join(previous_challenges[-10:])

        prompt = f"""
You are MoodSpark, a fun creative challenge AI.

User mood: {mood}

Create ONE tiny, fun and creative challenge.

IMPORTANT RULES:

- Use VERY SIMPLE English.
- Maximum 1 or 2 short sentences.
- Challenge must take only 2-5 minutes.
- Make it fun and interesting.
- Make the user want to actually do it.
- Do not give motivational speeches.
- Do not give therapy advice.
- Do not give exercise challenges.
- Give only ONE challenge.
- Make every challenge different.
- Do not repeat previous challenges.

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
CHALLENGE: Find 5 things around you that start with the letter S.
TIME: 3 minutes