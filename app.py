
from flask import Flask, render_template, request, jsonify
import requests
import os
import re
import random
import threading

app = Flask(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

OLLAMA_URL = "https://ollama.com/api/chat"
MODEL = "gpt-oss:120b"
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

# In-memory challenge history.
# Note: This resets on restart and is shared across users.
previous_challenges = []
history_lock = threading.Lock()

MOODS = {
    "happy": "Make it playful, silly and full of surprises.",
    "sad": "Make it gentle, comforting and easy to enjoy. No pressure.",
    "bored": "Make it unexpected, weird and exciting.",
    "tired": "Make it relaxing, simple and low-effort.",
    "angry": "Make it a harmless, funny way to express big feelings.",
    "anxious": "Make it calm, playful and easy to start.",
    "excited": "Make it imaginative, surprising and full of energy.",
    "curious": "Make it mysterious, clever and full of discovery.",
    "creative": "Make it original, imaginative and unusual."
}

CHALLENGE_TYPES = [
    "drawing",
    "writing",
    "puzzle",
    "brain",
    "craft",
    "creative",
    "imagination",
    "word game",
    "mini mystery",
    "silly invention",
    "story game",
    "observation"
]


# =========================================================
# OLLAMA API
# =========================================================

def ask_ollama(prompt):
    if not OLLAMA_API_KEY:
        raise RuntimeError(
            "OLLAMA_API_KEY is missing. "
            "Add it to your Render environment variables."
        )

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.9
        }
    }

    response = requests.post(
        OLLAMA_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    result = response.json()
    content = result.get("message", {}).get("content", "")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("The AI returned an empty response.")

    return content.strip()


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# GENERATE A CREATIVE CHALLENGE
# =========================================================

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json(silent=True) or {}

        mood = str(data.get("mood", "happy")).lower().strip()

        if mood not in MOODS:
            mood = "happy"

        with history_lock:
            recent = previous_challenges[-15:].copy()

        previous_text = "\n".join(recent) if recent else "None yet."

        challenge_type = random.choice(CHALLENGE_TYPES)
        mood_instruction = MOODS[mood]

        prompt = f"""
You are MoodSpark, a brilliant creator of tiny, joyful challenges.

YOUR GOAL:
Give the user one small activity that makes them think:
"Oh, that sounds fun! I want to try it!"

USER MOOD: {mood}
MOOD STYLE: {mood_instruction}

SUGGESTED CHALLENGE TYPE: {challenge_type}

RULES FOR EVERY CHALLENGE:

1. Use very simple English.
2. Use short sentences and familiar words.
3. The task must take 2 to 5 minutes.
4. Give ONE clear activity, not a list of unrelated tasks.
5. Make it playful, surprising, funny or imaginative.
6. The user should know exactly what to do.
7. Use ordinary objects, paper or imagination.
8. Do not require money, special tools or internet access.
9. No exercise, therapy, dangerous activities or embarrassing pranks.
10. Do not judge the user's mood or tell them how they should feel.
11. Do not give boring advice like "be positive" or "believe in yourself".
12. Never make the user feel bad if they cannot finish.
13. Drawing, writing, puzzles, crafts, word games,
    pretend inventions and mini mysteries are welcome.
14. Vary the IDEA, not just the wording.
15. Avoid generic tasks such as simply listing five objects.
16. Give the task a short, catchy title.
17. Make it suitable for a wide range of ages.

CREATIVITY TEST:

Prefer ideas with an unusual twist, funny situation,
imaginative rule, tiny mystery or surprising result.

Weak idea:
"Draw a cat."

Better idea:
"Draw a cat that runs a pizza shop on the moon.
Give it a silly name and invent its strangest pizza."

Weak idea:
"Write a story."

Better idea:
"Your socks have started a detective agency.
Write two clues about their first mystery."

Do not copy these examples. Invent fresh ideas.

RECENT CHALLENGES TO AVOID:
{previous_text}

Create a NEW challenge. Avoid repeating the same central idea,
activity, story setup or twist from the recent challenges.

Return ONLY this format:

TYPE: one short category
TITLE: a catchy title
CHALLENGE: 1 to 3 short sentences explaining what to do
TIME: 2-5 minutes

No introduction. No extra commentary.
"""

        challenge = ask_ollama(prompt)

        # Basic response validation
        if "CHALLENGE:" not in challenge.upper():
            raise RuntimeError(
                "The AI returned an invalid challenge format. Please try again."
            )

        with history_lock:
            previous_challenges.append(challenge)

            if len(previous_challenges) > 30:
                previous_challenges.pop(0)

        return jsonify({
            "success": True,
            "challenge": challenge
        })

    except requests.RequestException as e:
        app.logger.exception("Ollama API request failed")

        return jsonify({
            "success": False,
            "error": "The AI is having trouble connecting. Please try again."
        }), 502

    except Exception:
        app.logger.exception("Challenge generation failed")

        return jsonify({
            "success": False,
            "error": "Could not create a challenge right now. Please try again."
        }), 500


# =========================================================
# SUBMIT AND EVALUATE A CHALLENGE
# =========================================================

@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.get_json(silent=True) or {}

        mood = str(data.get("mood", "happy"))[:100]
        challenge = str(data.get("challenge", ""))[:3000].strip()
        submission = str(data.get("submission", ""))[:10000].strip()
        submission_type = str(
            data.get("submission_type", "text")
        )[:50]

        if not challenge:
            return jsonify({
                "success": False,
                "error": "Please select a challenge first."
            }), 400

        if not submission:
            return jsonify({
                "success": False,
                "error": "Please submit your challenge first."
            }), 400

        prompt = f"""
You are the friendly and fair judge of MoodSpark.

CHALLENGE:
{challenge}

USER'S MOOD:
{mood}

SUBMISSION TYPE:
{submission_type}

USER'S SUBMISSION:
{submission}

YOUR JOB:

Give a fair score from 1 to 10.

Consider:
- Creativity and original ideas.
- Effort shown in the submission.
- How well it follows the challenge.
- Funny, clever or interesting details.

SCORING GUIDE:
1-3: Very little of the task is shown.
4-5: A start has been made.
6-7: A good attempt with some interesting details.
8-9: Strong effort, creativity or a clever twist.
10: An especially original and well-executed response.

IMPORTANT:
- Do not automatically give 10.
- Do not be cruel or overly strict.
- Do not assume missing details.
- Evaluate the actual submission, not an imagined version.
- For simple attempts, recognize what the user did achieve.
- For image submissions, judge only details you can actually see.
- Never claim to have seen an image if only text was provided.
- Use simple English.
- Mention one specific detail from the submission.
- Keep the comment to 1 or 2 short sentences.
- Be encouraging without giving fake praise.

Return ONLY this format:

SCORE: 8/10
COMMENT: Your short, specific feedback.
"""

        feedback = ask_ollama(prompt)

        score_match = re.search(
            r"SCORE\s*:\s*(10|[1-9])\s*(?:/\s*10)?",
            feedback,
            re.IGNORECASE
        )

        comment_match = re.search(
            r"COMMENT\s*:\s*(.*)",
            feedback,
            re.IGNORECASE | re.DOTALL
        )

        if not score_match or not comment_match:
            raise RuntimeError(
                "The AI returned feedback in an unexpected format."
            )

        score = int(score_match.group(1))
        comment = comment_match.group(1).strip()

        # Keep feedback concise and remove accidental extra sections.
        comment = re.split(
            r"\n\s*(?:SCORE|TYPE|CHALLENGE)\s*:",
            comment,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0].strip()

        if not comment:
            comment = "Thanks for giving this challenge a try!"

        return jsonify({
            "success": True,
            "score": f"{score}/10",
            "feedback": comment
        })

    except requests.RequestException:
        app.logger.exception("Ollama evaluation request failed")

        return jsonify({
            "success": False,
            "error": "Could not evaluate your work right now. Please try again."
        }), 502

    except Exception:
        app.logger.exception("Challenge evaluation failed")

        return jsonify({
            "success": False,
            "error": "Could not evaluate your submission. Please try again."
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
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
