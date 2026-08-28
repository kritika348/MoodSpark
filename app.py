from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(**name**)

# =========================

# OLLAMA CLOUD

# =========================

OLLAMA_URL = "https://ollama.com/api/chat"

MODEL = "gemma3:4b"

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

previous_challenges = []

# =========================

# OLLAMA REQUEST

# =========================

def ask_ollama(prompt, image_base64=None):

```
if not OLLAMA_API_KEY:
    raise Exception("OLLAMA_API_KEY is not configured on Render.")

message = {
    "role": "user",
    "content": prompt
}

# Add image for drawing/image evaluation
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

print("Ollama status:", response.status_code)
print("Ollama response:", response.text)

response.raise_for_status()

result = response.json()

return result["message"]["content"]
```

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

```
data = request.get_json()

mood = data.get("mood", "")

previous = "\n".join(previous_challenges[-10:])

prompt = f"""
```

You are MoodSpark, a fun creative challenge AI.

User mood: {mood}

Create ONE fun mini challenge.

Rules:

* Use VERY SIMPLE English.
* Keep it extremely short.
* Maximum 1-2 sentences.
* It must take only 2-5 minutes.
* Make it playful and creative.
* Make the user want to try it.
* Do not give motivational speeches.
* Do not give therapy or medical advice.
* Do not give exercise challenges.
* Give a different challenge every time.
* Do not repeat previous challenges.

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

CHALLENGE: short challenge

TIME: 2-5 minutes
"""

```
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
```

# =========================

# SUBMIT + AI EVALUATION

# =========================

@app.route("/submit", methods=["POST"])
def submit():

```
data = request.get_json()

mood = data.get("mood", "")
challenge = data.get("challenge", "")
submission = data.get("submission", "")
submission_type = data.get("submission_type", "text")

image_base64 = None

if submission_type in ["drawing", "image"]:
    image_base64 = submission


# =========================
# IMAGE / DRAWING EVALUATION
# =========================

if image_base64:

    feedback_prompt = f"""
```

You are the friendly creative judge of MoodSpark.

User mood:
{mood}

Challenge:
{challenge}

The user submitted an image showing their completed challenge.

Look carefully at the image.

Judge it based on:

* Effort
* Creativity
* How well it follows the challenge
* Originality

Be encouraging, especially for beginners.

Give a genuine score from 1 to 10.

Do NOT automatically give 10/10.

Mention something specific you noticed in the image.

Keep the comment impressive, friendly and positive.

Maximum 2 sentences.

Return ONLY:

SCORE: X/10

COMMENT:
Your personalized comment.
"""

```
else:

    feedback_prompt = f"""
```

You are the friendly creative judge of MoodSpark.

User mood:
{mood}

Challenge:
{challenge}

User's answer:
{submission}

Judge it based on:

* Effort
* Creativity
* How well it completes the challenge
* Originality

Give a genuine score from 1 to 10.

Do NOT automatically give 10/10.

Be positive and encouraging.

Mention something specific about the answer.

Maximum 2 sentences.

Return ONLY:

SCORE: X/10

COMMENT:
Your personalized comment.
"""

```
try:

    feedback = ask_ollama(
        feedback_prompt,
        image_base64=image_base64
    )

    score = "—"

    for line in feedback.splitlines():

        if "SCORE:" in line.upper():

            score = line.split(":", 1)[1].strip()

            break


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

    print(
        "Ollama Evaluation Error:",
        str(e)
    )

    return jsonify({

        "error": str(e)

    }), 500
```

# =========================

# START SERVER

# =========================

if **name** == "**main**":

```
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
```
