/* =========================================================
   AI Video Assistant — app.js
   All backend endpoints, request bodies, field names and the
   API base URL are preserved exactly as specified.
   ========================================================= */

const API = "http://127.0.0.1:8000";

/* ---------- Markdown rendering helper (Marked.js + DOMPurify) ---------- */
function renderMarkdown(rawText) {
  const text = (rawText === undefined || rawText === null || rawText === "")
    ? ""
    : String(rawText);

  if (!text) return "";

  try {
    const dirtyHtml = marked.parse(text, { breaks: true, gfm: true });
    if (typeof DOMPurify !== "undefined") {
      return DOMPurify.sanitize(dirtyHtml);
    }
    return dirtyHtml;
  } catch (err) {
    console.error("Markdown render error:", err);
    // Fall back to escaped plain text so nothing unsafe is ever injected
    const escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return `<p>${escaped}</p>`;
  }
}

function setMarkdown(el, rawText) {
  el.innerHTML = renderMarkdown(rawText);
}

/* ---------- Element references ---------- */
const dropzone = document.getElementById("dropzone");
const videoFile = document.getElementById("videoFile");
const fileChip = document.getElementById("fileChip");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const fileClear = document.getElementById("fileClear");

const youtubeUrl = document.getElementById("youtubeUrl");
const languageSelect = document.getElementById("language");

const analyzeBtn = document.getElementById("analyzeBtn");
const analyzeError = document.getElementById("analyzeError");
const analyzeErrorMsg = document.getElementById("analyzeErrorMsg");

const loadingSection = document.getElementById("loadingSection");
const loadingSteps = document.querySelectorAll("#loadingSteps li");

const resultsSection = document.getElementById("resultsSection");
const resultTitle = document.getElementById("resultTitle");
const resultSummary = document.getElementById("resultSummary");
const resultActionItems = document.getElementById("resultActionItems");
const resultKeyDecisions = document.getElementById("resultKeyDecisions");
const resultOpenQuestions = document.getElementById("resultOpenQuestions");
const transcriptViewer = document.getElementById("transcriptViewer");
const transcriptSearch = document.getElementById("transcriptSearch");

const chatBox = document.getElementById("chatBox");
const chatEmpty = document.getElementById("chatEmpty");
const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("question");
const sendBtn = document.getElementById("sendBtn");

let isAnalyzing = false;
let isSending = false;
let selectedFile = null;
let rawTranscript = "";

/* =========================================================
   FILE UPLOAD / DROPZONE
   ========================================================= */

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function setSelectedFile(file) {
  selectedFile = file || null;
  if (selectedFile) {
    fileName.textContent = selectedFile.name;
    fileSize.textContent = formatBytes(selectedFile.size);
    fileChip.hidden = false;
  } else {
    fileChip.hidden = true;
    videoFile.value = "";
  }
}

dropzone.addEventListener("click", (e) => {
  if (e.target.closest(".file-clear")) return;
  videoFile.click();
});

dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    videoFile.click();
  }
});

videoFile.addEventListener("change", () => {
  setSelectedFile(videoFile.files && videoFile.files[0]);
});

["dragenter", "dragover"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add("drag-over");
  });
});

["dragleave", "drop"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("drag-over");
  });
});

dropzone.addEventListener("drop", (e) => {
  const dt = e.dataTransfer;
  if (dt && dt.files && dt.files.length) {
    const file = dt.files[0];
    // Keep the native input in sync so nothing else needs to change
    try {
      const transfer = new DataTransfer();
      transfer.items.add(file);
      videoFile.files = transfer.files;
    } catch (err) {
      console.warn("Could not sync dropped file to input:", err);
    }
    setSelectedFile(file);
  }
});

fileClear.addEventListener("click", (e) => {
  e.stopPropagation();
  setSelectedFile(null);
});

/* =========================================================
   ANALYZE FLOW
   ========================================================= */

function hideError() {
  analyzeError.hidden = true;
  analyzeErrorMsg.textContent = "";
}

function showError(message) {
  analyzeErrorMsg.textContent = message || "Unable to process this video. Please check the source and try again.";
  analyzeError.hidden = false;
}

async function extractErrorMessage(response) {
  try {
    const data = await response.json();
    if (typeof data === "string") return data;
    if (data && typeof data.detail === "string") return data.detail;
    if (data && Array.isArray(data.detail)) {
      return data.detail.map((d) => d.msg || JSON.stringify(d)).join(" ");
    }
    if (data && typeof data.message === "string") return data.message;
    if (data && typeof data.error === "string") return data.error;
    return `Request failed with status ${response.status}.`;
  } catch (err) {
    return `Request failed with status ${response.status}.`;
  }
}

function setAnalyzeLoading(isLoading) {
  isAnalyzing = isLoading;
  analyzeBtn.disabled = isLoading;
  analyzeBtn.querySelector(".btn-label").textContent = isLoading ? "Analyzing..." : "Analyze video";
  analyzeBtn.querySelector(".btn-spinner").hidden = !isLoading;
}

function resetLoadingSteps() {
  loadingSteps.forEach((li) => li.classList.remove("done", "active"));
}

function advanceLoadingStep(index) {
  loadingSteps.forEach((li) => {
    const step = Number(li.dataset.step);
    if (step < index) {
      li.classList.add("done");
      li.classList.remove("active");
    } else if (step === index) {
      li.classList.add("active");
      li.classList.remove("done");
    } else {
      li.classList.remove("done", "active");
    }
  });
}

function showLoading() {
  resultsSection.hidden = true;
  loadingSection.hidden = false;
  resetLoadingSteps();
  advanceLoadingStep(0);

  // Purely illustrative progression through the fixed steps — no fake
  // percentages, just an indication that processing is under way.
  let step = 0;
  const timer = setInterval(() => {
    step += 1;
    if (step > 2) {
      clearInterval(timer);
      return;
    }
    advanceLoadingStep(step);
  }, 1400);

  return () => {
    clearInterval(timer);
    loadingSteps.forEach((li) => li.classList.add("done"));
    loadingSteps.forEach((li) => li.classList.remove("active"));
  };
}

function hideLoading() {
  loadingSection.hidden = true;
}

function renderResults(result) {
  resultTitle.textContent = result.title || "Untitled analysis";
  setMarkdown(resultSummary, result.summary);
  setMarkdown(resultActionItems, result.action_items);
  setMarkdown(resultKeyDecisions, result.key_decisions);
  setMarkdown(resultOpenQuestions, result.open_questions);

  rawTranscript = result.transcript || "";
  transcriptViewer.textContent = rawTranscript || "No transcript available.";

  resultsSection.hidden = false;
  enableChat();
}

analyzeBtn.addEventListener("click", async () => {
  if (isAnalyzing) return;

  hideError();

  const lang = languageSelect.value;
  const url = youtubeUrl.value.trim();

  if (!selectedFile && !url) {
    showError("Please upload a video file or paste a YouTube URL before analyzing.");
    return;
  }

  setAnalyzeLoading(true);
  const finishSteps = showLoading();

  try {
    let response;

    if (selectedFile) {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("language", lang);

      response = await fetch(`${API}/analyze/file`, {
        method: "POST",
        body: formData
      });
    } else {
      response = await fetch(`${API}/analyze/youtube`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          source: url,
          language: lang
        })
      });
    }

    if (!response.ok) {
      const message = await extractErrorMessage(response);
      throw new Error(message);
    }

    const result = await response.json();
    advanceLoadingStep(3);
    finishSteps();
    renderResults(result);
  } catch (err) {
    console.error("Analyze request failed:", err);
    showError(err.message || "Unable to process this video. Please check the source and try again.");
  } finally {
    finishSteps();
    hideLoading();
    setAnalyzeLoading(false);
  }
});

/* =========================================================
   TRANSCRIPT SEARCH (client-side highlight only)
   ========================================================= */

function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

transcriptSearch.addEventListener("input", () => {
  const query = transcriptSearch.value.trim();

  if (!query) {
    transcriptViewer.textContent = rawTranscript || "No transcript available.";
    return;
  }

  const escaped = escapeHtml(rawTranscript || "");
  const pattern = new RegExp(escapeRegExp(escapeHtml(query)), "gi");
  transcriptViewer.innerHTML = escaped.replace(pattern, (match) => `<mark>${match}</mark>`);
});

/* =========================================================
   CHAT FLOW
   ========================================================= */

function enableChat() {
  if (chatEmpty) chatEmpty.hidden = true;
}

function scrollChatToBottom() {
  chatBox.scrollTop = chatBox.scrollHeight;
}

function formatTimestamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function appendUserMessage(text) {
  const wrap = document.createElement("div");
  wrap.className = "chat-msg user";
  wrap.innerHTML = `
    <div class="chat-bubble"></div>
    <span class="chat-timestamp">${formatTimestamp()}</span>
  `;
  wrap.querySelector(".chat-bubble").textContent = text;
  chatBox.appendChild(wrap);
  scrollChatToBottom();
  return wrap;
}

function appendThinkingMessage() {
  const wrap = document.createElement("div");
  wrap.className = "chat-msg ai";
  wrap.innerHTML = `
    <div class="chat-bubble">
      <div class="chat-thinking"><span></span><span></span><span></span></div>
    </div>
  `;
  chatBox.appendChild(wrap);
  scrollChatToBottom();
  return wrap;
}

function replaceWithAiMessage(thinkingEl, answerText) {
  thinkingEl.innerHTML = `
    <div class="chat-bubble"><div class="markdown-body"></div></div>
    <span class="chat-timestamp">${formatTimestamp()}</span>
  `;
  setMarkdown(thinkingEl.querySelector(".markdown-body"), answerText);
  scrollChatToBottom();
}

function replaceWithErrorMessage(thinkingEl, message) {
  thinkingEl.className = "chat-msg ai error";
  thinkingEl.innerHTML = `
    <div class="chat-bubble">${escapeHtml(message)}</div>
    <span class="chat-timestamp">${formatTimestamp()}</span>
  `;
  scrollChatToBottom();
}

function setSendLoading(isLoading) {
  isSending = isLoading;
  sendBtn.disabled = isLoading;
  sendBtn.querySelector(".send-icon").hidden = isLoading;
  sendBtn.querySelector(".btn-spinner").hidden = !isLoading;
}

async function sendQuestion(question) {
  const thinkingEl = appendThinkingMessage();
  setSendLoading(true);

  try {
    const response = await fetch(`${API}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        question: question
      })
    });

    if (!response.ok) {
      const message = await extractErrorMessage(response);
      throw new Error(message);
    }

    const data = await response.json();
    replaceWithAiMessage(thinkingEl, data.answer);
  } catch (err) {
    console.error("Chat request failed:", err);
    replaceWithErrorMessage(thinkingEl, err.message || "Something went wrong answering that question. Please try again.");
  } finally {
    setSendLoading(false);
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  if (isSending) return;

  const question = questionInput.value.trim();
  if (!question) return;

  appendUserMessage(question);
  questionInput.value = "";
  autoGrowTextarea();
  sendQuestion(question);
});

questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});

function autoGrowTextarea() {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 140)}px`;
}
questionInput.addEventListener("input", autoGrowTextarea);
