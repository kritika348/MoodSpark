// ==================================================
// MOODSPARK — GAME CONTROLLER
// Compatible with Flask /generate and /submit routes
// ==================================================

let selectedMood = "";
let selectedMode = "";
let currentChallenge = "";
let drawingHistory = [];
let isDrawing = false;
let timerInterval = null;
let timeLeft = 0;
let totalXP = 0;
let hasSubmitted = false;
let currentGameData = null;
let selectedAnswer = "";
let gameFinished = false;

// ==================================================
// DOM ELEMENTS
// ==================================================

const $ = (id) => document.getElementById(id);

const moodCards = document.querySelectorAll(".mood-card");
const modeCards = document.querySelectorAll(".mode-card");

const moodSection = $("moodSection");
const gameModeSection = $("gameModeSection");
const challengeSection = $("challengeSection");
const loading = $("loading");

const challengeText = $("challengeText");
const challengeTitle = $("challengeTitle");
const challengeIcon = $("challengeIcon");
const challengeMeta = $("challengeMeta");

const textSubmission = $("textSubmission");
const drawingSubmission = $("drawingSubmission");
const submission = $("submission");

const feedback = $("feedback");
const feedbackText = $("feedbackText");
const scoreText = $("scoreText");
const feedbackHeading = $("feedbackHeading");
const earnedXp = $("earnedXp");

const submitBtn = $("submitBtn");
const anotherBtn = $("anotherBtn");

const miniGameArea = $("miniGameArea");
const gamePrompt = $("gamePrompt");
const gameOptions = $("gameOptions");
const gameResult = $("gameResult");
const hintBtn = $("hintBtn");

const gameTimer = $("gameTimer");
const xpValue = $("xpValue");

const canvas = $("drawingCanvas");
const ctx = canvas.getContext("2d");

// ==================================================
// GAME CONFIGURATION
// ==================================================

const gameConfig = {
  puzzle: {
    title: "Puzzle Pop",
    icon: "🧩",
    seconds: 30
  },
  funny: {
    title: "LOL Factory",
    icon: "🤣",
    seconds: 60
  },
  word: {
    title: "Word Wizard",
    icon: "🔤",
    seconds: 30
  },
  brain: {
    title: "Brain Trap",
    icon: "🧠",
    seconds: 30
  },
  drawing: {
    title: "Doodle Dash",
    icon: "🎨",
    seconds: 120
  },
  creative: {
    title: "Weird Mode",
    icon: "👽",
    seconds: 120
  }
};

// ==================================================
// TOAST NOTIFICATIONS
// ==================================================

let toastTimeout;

function showToast(message) {
  const toast = $("toast");

  toast.textContent = message;
  toast.classList.remove("hidden");

  clearTimeout(toastTimeout);

  toastTimeout = setTimeout(() => {
    toast.classList.add("hidden");
  }, 3000);
}

// ==================================================
// MOOD SELECTION
// ==================================================

moodCards.forEach((card) => {
  card.addEventListener("click", () => {
    moodCards.forEach((item) => {
      item.classList.remove("selected");
      item.setAttribute("aria-pressed", "false");
    });

    card.classList.add("selected");
    card.setAttribute("aria-pressed", "true");

    selectedMood = card.dataset.mood;

    showToast("Your vibe: " + card.querySelector("span:last-child").textContent);
  });
});

// ==================================================
// GAME MODE SELECTION
// ==================================================

modeCards.forEach((card) => {
  card.addEventListener("click", () => {
    modeCards.forEach((item) => {
      item.classList.remove("selected");
      item.setAttribute("aria-pressed", "false");
    });

    card.classList.add("selected");
    card.setAttribute("aria-pressed", "true");

    selectedMode = card.dataset.mode;
  });
});

// ==================================================
// RANDOM SELECTION
// ==================================================

function chooseRandomMood() {
  const index = Math.floor(Math.random() * moodCards.length);
  moodCards[index].click();
}

function chooseRandomMode() {
  const index = Math.floor(Math.random() * modeCards.length);
  modeCards[index].click();
}

$("surpriseBtn").addEventListener("click", () => {
  chooseRandomMood();
  chooseRandomMode();

  showToast("Surprise mode activated! 🎲");

  generateChallenge();
});

// ==================================================
// TIMER
// ==================================================

function stopTimer() {
  if (timerInterval !== null) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function startTimer(seconds) {
  stopTimer();

  timeLeft = seconds;
  updateTimerDisplay();

  timerInterval = setInterval(() => {
    if (timeLeft > 0) {
      timeLeft--;
      updateTimerDisplay();
    } else {
      stopTimer();

      if (gameTimer) {
        gameTimer.textContent = "⏰ TIME'S UP!";
        gameTimer.classList.add("urgent");
      }

      showToast("Time's up! You can still submit your answer.");
    }
  }, 1000);
}

function updateTimerDisplay() {
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  gameTimer.textContent =
    "⏱ " +
    String(minutes).padStart(2, "0") +
    ":" +
    String(seconds).padStart(2, "0");

  gameTimer.classList.toggle("urgent", timeLeft <= 10);
}

// ==================================================
// CANVAS SETUP
// ==================================================

function setupCanvas() {
  if (!canvas || canvas.clientWidth === 0) return;

  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;

  canvas.width = Math.round(rect.width * ratio);
  canvas.height = Math.round(rect.height * ratio);

  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, rect.width, rect.height);

  ctx.lineWidth = 4;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.strokeStyle = "#292333";

  drawingHistory = [];

  $("drawingStatus").textContent = "Go wild!";
}

function getPosition(event) {
  const rect = canvas.getBoundingClientRect();

  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  };
}

function saveCanvas() {
  if (canvas.width && canvas.height) {
    drawingHistory.push(canvas.toDataURL("image/png"));

    if (drawingHistory.length > 30) {
      drawingHistory.shift();
    }
  }
}

function startDrawing(event) {
  if (hasSubmitted) return;

  event.preventDefault();

  isDrawing = true;
  saveCanvas();

  const position = getPosition(event);

  ctx.beginPath();
  ctx.moveTo(position.x, position.y);
}

function draw(event) {
  if (!isDrawing) return;

  event.preventDefault();

  const position = getPosition(event);

  ctx.lineTo(position.x, position.y);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(position.x, position.y);

  $("drawingStatus").textContent = "✏️ Drawing...";
}

function stopDrawing(event) {
  if (!isDrawing) return;

  if (event) event.preventDefault();

  isDrawing = false;
  ctx.beginPath();

  $("drawingStatus").textContent = "✨ Nice!";
}

canvas.addEventListener("pointerdown", startDrawing);
canvas.addEventListener("pointermove", draw);
canvas.addEventListener("pointerup", stopDrawing);
canvas.addEventListener("pointercancel", stopDrawing);
canvas.addEventListener("pointerleave", stopDrawing);

// ==================================================
// CLEAR CANVAS
// ==================================================

$("clearCanvas").addEventListener("click", () => {
  if (hasSubmitted) return;

  const rect = canvas.getBoundingClientRect();

  ctx.clearRect(0, 0, rect.width, rect.height);

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, rect.width, rect.height);

  drawingHistory = [];

  $("drawingStatus").textContent = "Canvas cleared";
});

// ==================================================
// UNDO DRAWING
// ==================================================

function restoreCanvas(data) {
  const image = new Image();

  image.onload = () => {
    const rect = canvas.getBoundingClientRect();

    ctx.clearRect(0, 0, rect.width, rect.height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, rect.width, rect.height);

    ctx.drawImage(image, 0, 0, rect.width, rect.height);
  };

  image.src = data;
}

$("undoCanvas").addEventListener("click", () => {
  if (hasSubmitted) return;

  if (!drawingHistory.length) {
    showToast("Nothing to undo yet!");
    return;
  }

  restoreCanvas(drawingHistory.pop());

  $("drawingStatus").textContent = "↩️ Undo complete";
});

// ==================================================
// CHALLENGE SUBMISSION TYPE
// ==================================================

function showSubmissionType(challenge) {
  const isDrawing =
    typeof challenge === "string" &&
    /type\s*:\s*drawing/i.test(challenge);

  if (selectedMode === "drawing") {
    textSubmission.classList.add("hidden");
    drawingSubmission.classList.remove("hidden");

    requestAnimationFrame(setupCanvas);
  } else if (isDrawing) {
    textSubmission.classList.add("hidden");
    drawingSubmission.classList.remove("hidden");

    requestAnimationFrame(setupCanvas);
  } else {
    drawingSubmission.classList.add("hidden");
    textSubmission.classList.remove("hidden");
  }
}

// ==================================================
// OPTIONAL INTERACTIVE GAME DATA
// Supports /generate responses containing:
// { prompt, options: [], answer, hint }
// ==================================================

function setupMiniGame(data) {
  currentGameData = data;
  selectedAnswer = "";
  gameFinished = false;

  gameOptions.replaceChildren();
  gameResult.textContent = "";
  gameResult.classList.add("hidden");
  miniGameArea.classList.add("hidden");
  hintBtn.classList.remove("hidden");

  if (
    !data ||
    !Array.isArray(data.options) ||
    data.options.length < 2
  ) {
    return;
  }

  miniGameArea.classList.remove("hidden");

  gamePrompt.textContent =
    data.prompt || "Choose your answer!";

  data.options.forEach((option) => {
    const button = document.createElement("button");

    button.type = "button";
    button.textContent = String(option);

    button.addEventListener("click", () => {
      if (gameFinished || hasSubmitted) return;

      selectedAnswer = String(option);

      gameOptions.querySelectorAll("button").forEach((item) => {
        item.classList.remove("selected");
      });

      button.classList.add("selected");
    });

    gameOptions.appendChild(button);
  });
}

// ==================================================
// HINT BUTTON
// ==================================================

hintBtn.addEventListener("click", () => {
  if (currentGameData && currentGameData.hint) {
    showToast("💡 " + currentGameData.hint);
    return;
  }

  const hints = {
    puzzle: "Look for a pattern. The smallest detail may matter!",
    funny: "The sillier your idea, the better!",
    word: "Try rearranging the letters into smaller groups.",
    brain: "Read the question carefully before answering.",
    drawing: "Start with simple shapes, then add details.",
    creative: "There are no perfect answers. Be imaginative!"
  };

  showToast(
    "💡 " +
    (hints[selectedMode] || "Take a breath and give it a try!")
  );
});

// ==================================================
// RESET CHALLENGE STATE
// ==================================================

function resetChallengeState() {
  stopTimer();

  hasSubmitted = false;
  currentGameData = null;
  selectedAnswer = "";
  gameFinished = false;

  submission.value = "";

  feedback.classList.add("hidden");
  miniGameArea.classList.add("hidden");
  gameResult.classList.add("hidden");

  submitBtn.disabled = false;
  submitBtn.textContent = "🚀 Lock in my answer";

  gameTimer.classList.remove("urgent");
  gameTimer.textContent = "⏱ YOUR TURN";

  $("earnedXp").textContent = "";
  $("feedbackHeading").textContent = "The judge has spoken!";
}

// ==================================================
// GENERATE CHALLENGE
// ==================================================

async function generateChallenge() {
  if (!selectedMood || !selectedMode) {
    showToast("Pick a mood and a game mode first 😊");
    return;
  }

  resetChallengeState();

  loading.classList.remove("hidden");
  moodSection.classList.add("hidden");
  gameModeSection.classList.add("hidden");
  challengeSection.classList.add("hidden");

  try {
    const response = await fetch("/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        mood: selectedMood,
        mode: selectedMode
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Could not create challenge.");
    }

    if (!data.challenge) {
      throw new Error("The server returned an empty challenge.");
    }

    currentChallenge = data.challenge;

    challengeText.textContent = currentChallenge;

    const config = gameConfig[selectedMode] || gameConfig.creative;

    challengeTitle.textContent = config.title;
    challengeIcon.textContent = config.icon;
    challengeMeta.textContent =
      selectedMood + " mood • " + config.seconds + " seconds • Have fun!";

    showSubmissionType(currentChallenge);

    setupMiniGame(data.game || data);

    loading.classList.add("hidden");
    challengeSection.classList.remove("hidden");

    startTimer(config.seconds);

    challengeSection.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

  } catch (error) {
    console.error("Generate error:", error);

    loading.classList.add("hidden");
    moodSection.classList.remove("hidden");
    gameModeSection.classList.remove("hidden");

    showToast(error.message || "Could not create challenge. Try again.");
  }
}

// ==================================================
// CREATE BUTTON
// ==================================================

$("createBtn").addEventListener("click", generateChallenge);

// ==================================================
// SUBMIT ANSWER FOR AI EVALUATION
// ==================================================

submitBtn.addEventListener("click", async () => {
  if (hasSubmitted) return;

  let submissionData = "";
  let submissionType = "text";

  if (!drawingSubmission.classList.contains("hidden")) {
    submissionType = "drawing";
    submissionData = canvas.toDataURL("image/png");
  } else if (
    !miniGameArea.classList.contains("hidden") &&
    selectedAnswer
  ) {
    submissionData = selectedAnswer;
  } else {
    submissionData = submission.value.trim();
  }

  if (!submissionData) {
    showToast("Complete the challenge before submitting 😊");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "🤖 AI is judging...";

  try {
    const response = await fetch("/submit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        mood: selectedMood,
        mode: selectedMode,
        challenge: currentChallenge,
        submission: submissionData,
        submission_type: submissionType
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Evaluation failed.");
    }

    hasSubmitted = true;
    stopTimer();

    const score = Number(data.score);

    scoreText.textContent = Number.isFinite(score)
      ? "⭐ Score: " + score
      : "⭐ Score: " + String(data.score);

    feedbackText.textContent =
      data.feedback || "Great job completing your challenge!";

    feedbackHeading.textContent = "The judge has spoken! 🏆";

    // Prefer XP returned by the server.
    // Otherwise award XP based on the score.
    let gainedXP = Number(data.xp);

    if (!Number.isFinite(gainedXP)) {
      gainedXP = Number.isFinite(score)
        ? Math.max(0, Math.round(score))
        : 0;
    }

    totalXP += gainedXP;

    xpValue.textContent = totalXP + " XP";

    earnedXp.textContent =
      "+" + gainedXP + " XP earned ✨";

    feedback.classList.remove("hidden");

    submitBtn.textContent = "🎉 Completed!";

    gameFinished = true;

    if (!miniGameArea.classList.contains("hidden")) {
      gameResult.textContent = "Answer submitted for evaluation!";
      gameResult.classList.remove("hidden");
    }

    challengeSection.scrollIntoView({
      behavior: "smooth",
      block: "end"
    });

  } catch (error) {
    console.error("Submit error:", error);

    submitBtn.disabled = false;
    submitBtn.textContent = "🚀 Lock in my answer";

    showToast(error.message || "Evaluation failed. Please try again.");
  }
});

// ==================================================
// NEXT CHALLENGE
// ==================================================

anotherBtn.addEventListener("click", () => {
  resetChallengeState();
  generateChallenge();
});

// ==================================================
// BACK TO MOOD AND MODE SELECTION
// ==================================================

function backToSelection() {
  stopTimer();

  loading.classList.add("hidden");
  challengeSection.classList.add("hidden");
  moodSection.classList.remove("hidden");
  gameModeSection.classList.remove("hidden");
}

// ==================================================
// INITIAL SETUP
// ==================================================

xpValue.textContent = totalXP + " XP";

if ("ResizeObserver" in window) {
  const canvasObserver = new ResizeObserver(() => {
    if (!drawingSubmission.classList.contains("hidden") && !isDrawing) {
      // Avoid erasing an existing drawing during normal resizing.
      // Canvas is freshly initialized for each drawing challenge.
    }
  });

  canvasObserver.observe(canvas);
}

console.log("✨ MoodSpark game controller loaded!");
