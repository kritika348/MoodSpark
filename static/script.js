let selectedMood = "";
let currentChallenge = "";
let drawingHistory = [];
let isDrawing = false;

// =====================================
// MOOD SELECTION
// =====================================

const moodCards = document.querySelectorAll(".mood-card");

moodCards.forEach((card) => {
  card.addEventListener("click", () => {
    moodCards.forEach((item) => {
      item.classList.remove("selected");
    });

    card.classList.add("selected");

    selectedMood = card.dataset.mood;
  });
});

// =====================================
// DOM ELEMENTS
// =====================================

const moodSection = document.getElementById("moodSection");
const challengeSection = document.getElementById("challengeSection");
const loading = document.getElementById("loading");

const challengeText = document.getElementById("challengeText");

const textSubmission = document.getElementById("textSubmission");
const imageSubmission = document.getElementById("imageSubmission");
const drawingSubmission = document.getElementById("drawingSubmission");

const submission = document.getElementById("submission");

const imageUpload = document.getElementById("imageUpload");
const imagePreview = document.getElementById("imagePreview");

const feedback = document.getElementById("feedback");
const feedbackText = document.getElementById("feedbackText");
const scoreText = document.getElementById("scoreText");

const submitBtn = document.getElementById("submitBtn");

// =====================================
// CANVAS
// =====================================

const canvas = document.getElementById("drawingCanvas");
const ctx = canvas.getContext("2d");

function setupCanvas() {
  const ratio = window.devicePixelRatio || 1;

  const rect = canvas.getBoundingClientRect();

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

setupCanvas();

window.addEventListener("resize", () => {
  if (!drawingSubmission.classList.contains("hidden")) {
    setupCanvas();
  }
});

// =====================================
// DRAWING POSITION
// =====================================

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

// =====================================
// START DRAWING
// =====================================

function startDrawing(event) {
  event.preventDefault();

  isDrawing = true;

  saveCanvas();

  const position = getPosition(event);

  ctx.beginPath();
  ctx.moveTo(position.x, position.y);
}

// =====================================
// DRAW
// =====================================

function draw(event) {
  if (!isDrawing) return;

  event.preventDefault();

  const position = getPosition(event);

  ctx.lineTo(position.x, position.y);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(position.x, position.y);

  document.getElementById("drawingStatus").innerText = "✏️ Drawing...";
}

// =====================================
// STOP DRAWING
// =====================================

function stopDrawing(event) {
  if (!isDrawing) return;

  event.preventDefault();

  isDrawing = false;

  ctx.beginPath();

  document.getElementById("drawingStatus").innerText = "✨ Nice!";
}

// =====================================
// MOUSE
// =====================================

canvas.addEventListener("mousedown", startDrawing);
canvas.addEventListener("mousemove", draw);
canvas.addEventListener("mouseup", stopDrawing);
canvas.addEventListener("mouseleave", stopDrawing);

// =====================================
// TOUCH
// =====================================

canvas.addEventListener("touchstart", startDrawing, { passive: false });

canvas.addEventListener("touchmove", draw, { passive: false });

canvas.addEventListener("touchend", stopDrawing, { passive: false });

// =====================================
// SAVE DRAWING
// =====================================

function saveCanvas() {
  drawingHistory.push(canvas.toDataURL("image/png"));

  if (drawingHistory.length > 20) {
    drawingHistory.shift();
  }
}

// =====================================
// RESTORE DRAWING
// =====================================

function restoreCanvas(data) {
  const image = new Image();

  image.onload = () => {
    const rect = canvas.getBoundingClientRect();

    ctx.clearRect(0, 0, rect.width, rect.height);

    ctx.drawImage(image, 0, 0, rect.width, rect.height);
  };

  image.src = data;
}

// =====================================
// CLEAR
// =====================================

document.getElementById("clearCanvas").addEventListener("click", () => {
  saveCanvas();

  const rect = canvas.getBoundingClientRect();

  ctx.fillStyle = "white";

  ctx.fillRect(0, 0, rect.width, rect.height);

  drawingHistory = [];

  document.getElementById("drawingStatus").innerText = "Canvas cleared";
});

// =====================================
// UNDO
// =====================================

document.getElementById("undoCanvas").addEventListener("click", () => {
  if (drawingHistory.length === 0) {
    return;
  }

  const previous = drawingHistory.pop();

  restoreCanvas(previous);
});

// =====================================
// IMAGE UPLOAD
// =====================================

imageUpload.addEventListener("change", () => {
  const file = imageUpload.files[0];

  if (!file) return;

  const reader = new FileReader();

  reader.onload = (event) => {
    imagePreview.src = event.target.result;

    imagePreview.classList.remove("hidden");
  };

  reader.readAsDataURL(file);
});

// =====================================
// DETECT CHALLENGE TYPE
// =====================================

function getChallengeType(challenge) {
  const firstLine = challenge.split("\n")[0].toLowerCase();

  if (firstLine.includes("drawing")) {
    return "drawing";
  }

  if (firstLine.includes("craft")) {
    return "image";
  }

  if (firstLine.includes("photo")) {
    return "image";
  }

  if (firstLine.includes("writing")) {
    return "text";
  }

  if (firstLine.includes("puzzle")) {
    return "text";
  }

  if (firstLine.includes("brain")) {
    return "text";
  }

  if (firstLine.includes("creative")) {
    // Creative challenges usually involve making something
    return "image";
  }

  return "text";
}

// =====================================
// SHOW SUBMISSION TYPE
// =====================================

function showSubmissionType(challenge) {
  const type = getChallengeType(challenge);

  textSubmission.classList.add("hidden");
  drawingSubmission.classList.add("hidden");
  imageSubmission.classList.add("hidden");

  // DRAWING
  if (type === "drawing") {
    drawingSubmission.classList.remove("hidden");

    setTimeout(() => {
      setupCanvas();
    }, 100);
  }

  // IMAGE
  else if (type === "image") {
    imageSubmission.classList.remove("hidden");
  }

  // TEXT
  else {
    textSubmission.classList.remove("hidden");
  }
}

// =====================================
// GENERATE CHALLENGE
// =====================================

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

    if (!response.ok) {
      throw new Error("Server error");
    }

    const data = await response.json();

    currentChallenge = data.challenge;

    challengeText.innerText = currentChallenge;

    showSubmissionType(currentChallenge);

    loading.classList.add("hidden");

    challengeSection.classList.remove("hidden");
  } catch (error) {
    console.error(error);

    loading.classList.add("hidden");

    moodSection.classList.remove("hidden");

    alert("Could not create your challenge. Please try again.");
  }
}

// =====================================
// CREATE BUTTON
// =====================================

document.getElementById("createBtn").addEventListener("click", () => {
  if (!selectedMood) {
    alert("Please select your mood first 😊");

    return;
  }

  generateChallenge();
});

// =====================================
// SUBMIT
// =====================================

submitBtn.addEventListener("click", async () => {
  let submissionData = "";
  let submissionType = "text";

  // =========================
  // DRAWING
  // =========================

  if (!drawingSubmission.classList.contains("hidden")) {
    submissionType = "drawing";

    submissionData = canvas.toDataURL("image/png");
  }

  // =========================
  // IMAGE
  // =========================
  else if (!imageSubmission.classList.contains("hidden")) {
    submissionType = "image";

    if (!imageUpload.files || !imageUpload.files[0]) {
      alert("Please upload your creation first 📸");

      return;
    }

    submissionData = imagePreview.src;
  }

  // =========================
  // TEXT
  // =========================
  else {
    submissionData = submission.value.trim();

    submissionType = "text";
  }

  if (!submissionData) {
    alert("Complete the challenge first 😊");

    return;
  }

  submitBtn.innerText = "🤖 AI is checking your work...";

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

    // SCORE

    scoreText.innerText = "⭐ " + data.score;

    // COMMENT

    feedbackText.innerText = data.feedback;

    feedback.classList.remove("hidden");

    submitBtn.innerText = "🎉 Completed!";
  } catch (error) {
    console.error(error);

    alert("AI could not evaluate your submission. Please try again.");

    submitBtn.innerText = "✅ Submit Challenge";

    submitBtn.disabled = false;
  }
});

// =====================================
// ANOTHER CHALLENGE
// =====================================

document.getElementById("anotherBtn").addEventListener("click", () => {
  submission.value = "";

  imageUpload.value = "";

  imagePreview.src = "";

  imagePreview.classList.add("hidden");

  drawingHistory = [];

  feedback.classList.add("hidden");

  submitBtn.disabled = false;

  submitBtn.innerText = "✅ Submit Challenge";

  generateChallenge();
});
