
from flask import Flask, render_template, request, jsonify
import requests
import os
import re
import json
import random
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
    "drawing": "Create a simple drawing challenge that can be done on a canvas or paper.",
    "creative": "Create an imaginative mini activity using ideas, stories or pretend inventions."
}

QUIZ_MODES = {"puzzle", "word", "brain"}


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


def extract_json(text):
    """Extract a JSON object even if the model adds code fences."""
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
        data = request.get_json(silent=True) or {}

        mood = str(data.get("mood", "happy")).lower().strip()
        mode = str(data.get("mode", "creative")).lower().strip()

        if mood not in MOODS:
            mood = "happy"

        if mode not in MODES:
            mode = "creative"

        with history_lock:
            recent = previous_challenges[-15:].copy()

        recent_text = "\n".join(recent) if recent else "None yet."

        quiz_instruction = ""
        if mode in QUIZ_MODES:
            quiz_instruction = """
For this mode, also create a multiple-choice mini-game:
- "game_prompt": one clear question.
- "options": exactly four short answer options.
- "answer": the exact text of the correct option.
- "hint": one short helpful clue.
The answer must match one of the four options exactly.
Do not reveal the answer in the challenge text.
"""
        else:
            quiz_instruction = """
This is an activity mode, not a multiple-choice quiz.
Set "game_prompt", "options", "answer" and "hint" to empty strings or an empty array.
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
- Does not pressure or embarrass the user.
- Avoids repeating the same central idea from recent challenges.
- Has a short, catchy title.
- Fits the selected game mode.

RECENT CHALLENGES TO AVOID:
{recent_text}

{quiz_instruction}

Return ONLY a valid JSON object using exactly these keys:
{{
  "type": "{mode}",
  "title": "Short catchy title",
  "challenge_text": "One to three short sentences explaining the activity.",
  "time": "2-5 minutes",
  "game_prompt": "Question for quiz modes, otherwise empty string",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "answer": "Correct option text for quiz modes, otherwise empty string",
  "hint": "Short hint for quiz modes, otherwise empty string"
}}

For non-quiz modes, "options" must be [].
Do not include Markdown or any text outside the JSON.
"""

        raw_response = ask_ollama(prompt)
        result = extract_json(raw_response)

        title = str(result.get("title", "Your Tiny Challenge")).strip()
        challenge_text = str(result.get("challenge_text", "")).strip()
        challenge_type = str(result.get("type", mode)).strip()
        time_text = str(result.get("time", "2-5 minutes")).strip()

        if not challenge_text:
            raise ValueError("The AI did not provide challenge instructions.")

        # Keep the challenge in the format used by the existing frontend.
        challenge = (
            f"TYPE: {challenge_type}\n"
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

            # Validate the quiz data before sending it to the browser.
            if (
                isinstance(options, list)
                and len(options) == 4
                and all(isinstance(option, str) for option in options)
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

        history_entry = f"{mode}: {title} - {challenge_text}"

        with history_lock:
            previous_challenges.append(history_entry)

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
        data = request.get_json(silent=True) or {}

        mood = str(data.get("mood", "happy")).lower().strip()[:50]
        mode = str(data.get("mode", "creative")).lower().strip()[:50]
        challenge = str(data.get("challenge", "")).strip()[:3000]
        submission = str(data.get("submission", "")).strip()[:10000]
        submission_type = str(
            data.get("submission_type", "text")
        ).lower().strip()[:50]

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

        # This model is not assumed to have image-vision capabilities.
        # Do not send a canvas base64 image to the model as ordinary text.
        if submission.startswith("data:image/"):
            return jsonify({
                "success": True,
                "score": "7/10",
                "feedback": (
                    "Your drawing was submitted! This model cannot inspect "
                    "the image itself, so this is a placeholder score rather "
                    "than a visual evaluation."
                ),
                "xp": 70,
                "earned_xp": 70
            })

        prompt = f"""
You are the friendly and fair judge of MoodSpark.

CHALLENGE:
{challenge}

USER MOOD:
{mood}

GAME MODE:
{mode}

SUBMISSION TYPE:
{submission_type}

USER SUBMISSION:
{submission}

Give a fair score from 1 to 10 based on the actual submission.
Consider effort, creativity and how well it follows the challenge.

Scoring guide:
1-3: Very little of the task is shown.
4-5: A start has been made.
6-7: A good attempt with some interesting details.
8-9: Strong effort or a clever idea.
10: Especially original and well-executed.

Be encouraging but honest. Do not assume missing details.
Use simple English. Mention one specific detail if possible.
Keep the comment to one or two short sentences.

Return ONLY valid JSON in this format:
{{
  "score": 8,
  "comment": "Short, specific and friendly feedback."
}}
"""

        raw_feedback = ask_ollama(prompt)
        result = extract_json(raw_feedback)

        try:
            score = int(result.get("score", 0))
        except (ValueError, TypeError):
            score = 0

        if score < 1 or score > 10:
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
