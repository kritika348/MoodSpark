
from flask import Flask, render_template, request, jsonify
import requests
import csv
from datetime import datetime
import os
import re
import json
import threading

app = Flask(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

OLLAMA_URL = "https://ollama.com/api/chat"
MODEL = "gpt-oss:120b"
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

previous_challenges = []
history_lock = threading.Lock()
feedback_lock = threading.Lock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FEEDBACK_FILE = os.path.join(BASE_DIR, "feedback.csv")

MOODS = {
    "happy": "playful, silly and full of surprises",
    "sad": "gentle, comforting and easy to enjoy",
    "bored": "unexpected, weird and exciting",
    "tired": "relaxing, simple and low-effort",
    "angry": "harmless, funny and expressive",
    "anxious": "calm, playful and easy to start",
    "stressed": "calm, light and pressure-free",
    "excited": "imaginative, surprising and energetic",
    "curious": "mysterious, clever and full of discovery",
    "creative": "original, imaginative and unusual"
}

MODES = {
    "puzzle": "Create a short, clever puzzle or riddle.",
    "funny": "Create a silly, funny activity with an unexpected twist.",
    "word": "Create a quick word game, word puzzle or word challenge.",
    "brain": "Create a short logic or thinking challenge.",
    "drawing": "Create a simple drawing challenge for a canvas or paper.",
    "creative": "Create an imaginative mini activity using ideas, stories or pretend inventions."
}

QUIZ_MODES = {"puzzle", "word", "brain"}

FEEDBACK_FEELINGS = {
    "Happier",
    "Relaxed",
    "Same",
    "Still bored",
    "More excited"
}


# =========================================================
# OLLAMA API
# =========================================================

def ask_ollama(prompt):
    if not OLLAMA_API_KEY:
        raise RuntimeError(
            "OLLAMA_API_KEY is missing. Add it to Render environment variables."
        )

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.9}
    }

    response = requests.post(
        OLLAMA_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    content = response.json().get("message", {}).get("content", "")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("The AI returned an empty response.")

    return content.strip()


def extract_json(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)

        if not match:
            raise ValueError("The AI did not return valid JSON.")

        return json.loads(match.group(0))


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# GENERATE A CHALLENGE
# =========================================================

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "error": "Invalid request data."
            }), 400

        mood = str(data.get("mood", "happy")).lower().strip()
        mode = str(data.get("mode", "creative")).lower().strip()

        if mood not in MOODS:
            mood = "happy"

        if mode not in MODES:
            mode = "creative"

        with history_lock:
            recent = previous_challenges[-15:].copy()

        recent_text = "\n".join(recent) if recent else "None yet."

        if mode in QUIZ_MODES:
            quiz_instruction = """
Create a multiple-choice game.
Provide a clear question, exactly four different short options,
the correct answer matching one option exactly, and a short hint.
Do not reveal the answer in the challenge text.
"""
        else:
            quiz_instruction = """
This is not a multiple-choice quiz.
Set game_prompt, answer and hint to empty strings.
Set options to an empty array.
"""

        prompt = f"""
You are MoodSpark, a creative mini-game designer.

USER MOOD: {mood}
MOOD STYLE: {MOODS[mood]}
SELECTED GAME MODE: {mode}
MODE INSTRUCTIONS: {MODES[mode]}

Create ONE fresh activity that:
- Takes 2 to 5 minutes.
- Uses simple English and short sentences.
- Is fun, specific, safe and easy to start.
- Needs no money or special equipment.
- Is suitable for a wide range of ages.
- Avoids repeating recent challenges.
- Has a short, catchy title.

Recent challenges to avoid:
{recent_text}

{quiz_instruction}

Return ONLY a valid JSON object with these keys:
{{
  "type": "{mode}",
  "title": "Short catchy title",
  "challenge_text": "One to three short sentences",
  "time": "2-5 minutes",
  "game_prompt": "",
  "options": [],
  "answer": "",
  "hint": ""
}}

For quiz modes, provide the question, four options, correct answer
and hint. For other modes, keep quiz fields empty.
Do not include Markdown outside the JSON.
"""

        result = extract_json(ask_ollama(prompt))

        title = str(result.get("title", "Your Tiny Challenge")).strip()[:150]
        challenge_text = str(result.get("challenge_text", "")).strip()[:2000]
        time_text = str(result.get("time", "2-5 minutes")).strip()[:50]

        if not challenge_text:
            raise ValueError("The AI did not provide challenge instructions.")

        challenge = (
            f"TYPE: {mode}\n"
            f"TITLE: {title}\n"
            f"CHALLENGE: {challenge_text}\n"
            f"TIME: {time_text}"
        )

        game = None

        if mode in QUIZ_MODES:
            options = result.get("options", [])
            answer = str(result.get("answer", "")).strip()
            game_prompt = str(result.get("game_prompt", "")).strip()
            hint = str(result.get("hint", "")).strip()

            if (
                isinstance(options, list)
                and len(options) == 4
                and all(isinstance(o, str) and o.strip() for o in options)
                and len(set(options)) == 4
                and answer in options
                and game_prompt
            ):
                game = {
                    "prompt": game_prompt,
                    "options": options,
                    "answer": answer,
                    "hint": hint
                }
            else:
                raise ValueError("The AI returned incomplete quiz data.")

        with history_lock:
            previous_challenges.append(f"{mode}: {title} - {challenge_text}")

            if len(previous_challenges) > 30:
                previous_challenges.pop(0)

        return jsonify({
            "success": True,
            "mood": mood,
            "mode": mode,
            "type": mode,
            "title": title,
            "time": time_text,
            "challenge": challenge,
            "game": game
        })

    except requests.RequestException:
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
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "error": "Invalid submission data."
            }), 400

        mood = str(data.get("mood", "happy")).strip()[:50]
        mode = str(data.get("mode", "creative")).strip()[:50]
        challenge = str(data.get("challenge", "")).strip()[:3000]
        submission = str(data.get("submission", "")).strip()[:10000]
        submission_type = str(
            data.get("submission_type", "text")
        ).strip()[:50]

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

        if submission.startswith("data:image/"):
            return jsonify({
                "success": True,
                "score": "7/10",
                "feedback": (
                    "Your drawing was submitted! This is a placeholder score, "
                    "not an evaluation of the image itself."
                ),
                "xp": 70,
                "earned_xp": 70
            })

        prompt = f"""
You are the friendly and fair judge of MoodSpark.

CHALLENGE: {challenge}
USER MOOD: {mood}
GAME MODE: {mode}
SUBMISSION TYPE: {submission_type}
USER SUBMISSION: {submission}

Give an honest score from 1 to 10 based on effort, creativity,
and how well the submission follows the challenge.
Be encouraging but honest. Use simple English and one or two
short sentences. Mention a specific detail if possible.

Return ONLY valid JSON:
{{
  "score": 8,
  "comment": "Short, specific and friendly feedback."
}}
"""

        result = extract_json(ask_ollama(prompt))

        try:
            score = int(result.get("score", 0))
        except (ValueError, TypeError):
            score = 0

        if not 1 <= score <= 10:
            raise ValueError("The AI returned an invalid score.")

        comment = str(result.get("comment", "")).strip()
        if not comment:
            comment = "Thanks for giving this challenge a try!"

        xp = score * 10

        return jsonify({
            "success": True,
            "score": f"{score}/10",
            "feedback": comment,
            "xp": xp,
            "earned_xp": xp
        })

    except requests.RequestException:
        app.logger.exception("Ollama evaluation request failed")
        return jsonify({
            "success": False,
            "error": "Could not evaluate your submission right now."
        }), 502

    except Exception:
        app.logger.exception("Challenge evaluation failed")
        return jsonify({
            "success": False,
            "error": "Could not evaluate your submission. Please try again."
        }), 500


# =========================================================
# USER FEEDBACK SESSION
# =========================================================

@app.route("/feedback", methods=["POST"])
def save_feedback():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid feedback data."
        }), 400

    rating_value = data.get("rating")

    try:
        if isinstance(rating_value, bool):
            raise ValueError

        rating = int(rating_value)

        if str(rating_value).strip() != str(rating):
            raise ValueError

        if rating not in range(1, 6):
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Please select a rating from 1 to 5."
        }), 400

    feeling = data.get("feeling")

    if not isinstance(feeling, str) or feeling.strip() not in FEEDBACK_FEELINGS:
        return jsonify({
            "success": False,
            "error": "Please select how you feel."
        }), 400

    feeling = feeling.strip()
    message = data.get("message", "")

    if not isinstance(message, str):
        return jsonify({
            "success": False,
            "error": "Feedback message must be text."
        }), 400

    message = message.strip()

    if len(message) > 1000:
        return jsonify({
            "success": False,
            "error": "Feedback must be under 1000 characters."
        }), 400

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    try:
        with feedback_lock:
            file_exists = (
                os.path.exists(FEEDBACK_FILE)
                and os.path.getsize(FEEDBACK_FILE) > 0
            )

            with open(
                FEEDBACK_FILE,
                "a",
                newline="",
                encoding="utf-8"
            ) as file:
                writer = csv.writer(file)

                if not file_exists:
                    writer.writerow([
                        "timestamp",
                        "rating",
                        "feeling",
                        "message"
                    ])

                writer.writerow([
                    timestamp,
                    rating,
                    feeling,
                    message
                ])

        app.logger.info("MoodSpark feedback saved successfully.")

        return jsonify({
            "success": True,
            "message": "Thank you! Your feedback has been received."
        }), 200

    except OSError:
        app.logger.exception("Unable to save feedback")
        return jsonify({
            "success": False,
            "error": "Feedback could not be saved right now."
        }), 500


# =========================================================
# ROUTE CHECK — useful for testing deployment
# =========================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "model": MODEL,
        "message": "MoodSpark AI is running!"
    })


@app.route("/feedback", methods=["GET"])
def feedback_route_check():
    return jsonify({
        "success": True,
        "message": "Feedback route exists. Submit feedback using POST."
    }), 200


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

