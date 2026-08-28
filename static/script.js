// ==================================================
// VARIABLES
// ==================================================

let selectedMood = "";

let currentChallenge = "";

let drawingHistory = [];

let isDrawing = false;

// ==================================================
// DOM ELEMENTS
// ==================================================

const moodCards = document.querySelectorAll(".mood-card");

const moodSection = document.getElementById("moodSection");

const challengeSection = document.getElementById("challengeSection");

const loading = document.getElementById("loading");

const challengeText = document.getElementById("challengeText");

const textSubmission = document.getElementById("textSubmission");

const drawingSubmission = document.getElementById("drawingSubmission");

const submission = document.getElementById("submission");

const feedback = document.getElementById("feedback");

const feedbackText = document.getElementById("feedbackText");

const scoreText = document.getElementById("scoreText");

const submitBtn = document.getElementById("submitBtn");

const canvas = document.getElementById("drawingCanvas");

const ctx = canvas.getContext("2d");

// ==================================================
// MOOD SELECTION
// ==================================================

moodCards.forEach((card) => {
  card.addEventListener("click", () => {
    moodCards.forEach((item) => {
      item.classList.remove("selected");
    });

    card.classList.add("selected");

    selectedMood = card.dataset.mood;
  });
});

// ==================================================
// CANVAS SETUP
// ==================================================

function setupCanvas() {
  const rect = canvas.getBoundingClientRect();

  const ratio = window.devicePixelRatio || 1;

  canvas.width = rect.width * ratio;

  canvas.height = rect.height * ratio;

  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);

  ctx.fillStyle = "white";

  ctx.fillRect(0, 0, rect.width, rect.height);

  ctx.lineWidth = 4;

  ctx.lineCap = "round";

  ctx.lineJoin = "round";

  ctx.strokeStyle = "#292333";
}

// ==================================================
// POSITION
// ==================================================

function getPosition(event) {
  const rect = canvas.getBoundingClientRect();

  let clientX;

  let clientY;

  if (event.touches) {
    clientX = event.touches[0].clientX;

    clientY = event.touches[0].clientY;
  } else {
    clientX = event.clientX;

    clientY = event.clientY;
  }

  return {
    x: clientX - rect.left,

    y: clientY - rect.top,
  };
}

// ==================================================
// SAVE DRAWING
// ==================================================

function saveCanvas() {
  drawingHistory.push(canvas.toDataURL("image/png"));

  if (drawingHistory.length > 20) {
    drawingHistory.shift();
  }
}

// ==================================================
// START DRAWING
// ==================================================

function startDrawing(event) {
  event.preventDefault();

  isDrawing = true;

  saveCanvas();

  const position = getPosition(event);

  ctx.beginPath();

  ctx.moveTo(position.x, position.y);
}

// ==================================================
// DRAW
// ==================================================

function draw(event) {
  if (!isDrawing) {
    return;
  }

  event.preventDefault();

  const position = getPosition(event);

  ctx.lineTo(position.x, position.y);

  ctx.stroke();

  ctx.beginPath();

  ctx.moveTo(position.x, position.y);

  document.getElementById("drawingStatus").innerText = "✏️ Drawing...";
}

// ==================================================
// STOP DRAWING
// ==================================================

function stopDrawing(event) {
  if (!isDrawing) {
    return;
  }

  event.preventDefault();

  isDrawing = false;

  ctx.beginPath();

  document.getElementById("drawingStatus").innerText = "✨ Nice!";
}

// ==================================================
// MOUSE EVENTS
// ==================================================

canvas.addEventListener("mousedown", startDrawing);

canvas.addEventListener("mousemove", draw);

canvas.addEventListener("mouseup", stopDrawing);

canvas.addEventListener("mouseleave", stopDrawing);

// ==================================================
// TOUCH EVENTS
// ==================================================

canvas.addEventListener("touchstart", startDrawing, { passive: false });

canvas.addEventListener("touchmove", draw, { passive: false });

canvas.addEventListener("touchend", stopDrawing, { passive: false });

// ==================================================
// CLEAR CANVAS
// ==================================================

document.getElementById("clearCanvas").addEventListener("click", () => {
  saveCanvas();

  const rect = canvas.getBoundingClientRect();

  ctx.fillStyle = "white";

  ctx.fillRect(0, 0, rect.width, rect.height);

  drawingHistory = [];

  document.getElementById("drawingStatus").innerText = "Canvas cleared";
});

// ==================================================
// UNDO
// ==================================================

document.getElementById("undoCanvas").addEventListener("click", () => {
  if (drawingHistory.length === 0) {
    return;
  }

  const previous = drawingHistory.pop();

  restoreCanvas(previous);
});

// ==================================================
// RESTORE CANVAS
// ==================================================

function restoreCanvas(data) {
  const image = new Image();

  image.onload = () => {
    const rect = canvas.getBoundingClientRect();

    ctx.clearRect(0, 0, rect.width, rect.height);

    ctx.drawImage(image, 0, 0, rect.width, rect.height);
  };

  image.src = data;
}

// ==================================================
// DETECT SUBMISSION TYPE
// ==================================================

function showSubmissionType(challenge) {
  const lower = challenge.toLowerCase();

  const drawing = lower.includes("type: drawing");

  if (drawing) {
    textSubmission.classList.add("hidden");

    drawingSubmission.classList.remove("hidden");

    drawingHistory = [];

    setTimeout(setupCanvas, 100);
  } else {
    drawingSubmission.classList.add("hidden");

    textSubmission.classList.remove("hidden");
  }
}

// ==================================================
// GENERATE CHALLENGE
// ==================================================

async function generateChallenge() {
  loading.classList.remove("hidden");

  moodSection.classList.add("hidden");

  challengeSection.classList.add("hidden");

  feedback.classList.add("hidden");

  try {
    const response = await fetch("/generate", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        mood: selectedMood,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Could not create challenge");
    }

    currentChallenge = data.challenge;

    challengeText.innerText = currentChallenge;

    showSubmissionType(currentChallenge);

    loading.classList.add("hidden");

    challengeSection.classList.remove("hidden");
  } catch (error) {
    console.error(error);

    loading.classList.add("hidden");

    moodSection.classList.remove("hidden");

    alert("Could not create challenge. Please try again.");
  }
}

// ==================================================
// CREATE BUTTON
// ==================================================

document.getElementById("createBtn").addEventListener("click", () => {
  if (!selectedMood) {
    alert("Please select your mood first 😊");

    return;
  }

  generateChallenge();
});

// ==================================================
// SUBMIT
// ==================================================

submitBtn.addEventListener("click", async () => {
  let submissionData = "";

  let submissionType = "text";

  // DRAWING

  if (!drawingSubmission.classList.contains("hidden")) {
    submissionType = "drawing";

    submissionData = canvas.toDataURL("image/png");
  }

  // TEXT
  else {
    submissionData = submission.value.trim();
  }

  if (!submissionData) {
    alert("Complete the challenge first 😊");

    return;
  }

  submitBtn.innerText = "🤖 AI is judging...";

  submitBtn.disabled = true;

  try {
    const response = await fetch("/submit", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        mood: selectedMood,

        challenge: currentChallenge,

        submission: submissionData,

        submission_type: submissionType,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Evaluation failed");
    }

    scoreText.innerText = "⭐ " + data.score;

    feedbackText.innerText = data.feedback;

    feedback.classList.remove("hidden");

    submitBtn.innerText = "🎉 Completed!";
  } catch (error) {
    console.error(error);

    alert("AI evaluation failed. Please try again.");

    submitBtn.innerText = "✅ Submit Challenge";

    submitBtn.disabled = false;
  }
});

// ==================================================
// ANOTHER CHALLENGE
// ==================================================

document.getElementById("anotherBtn").addEventListener("click", () => {
  submission.value = "";

  drawingHistory = [];

  feedback.classList.add("hidden");

  submitBtn.disabled = false;

  submitBtn.innerText = "✅ Submit Challenge";

  generateChallenge();
});
