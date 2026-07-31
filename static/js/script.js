const targetLangSelect = document.getElementById("targetLang");
const sourceLangSelect = document.getElementById("sourceLang");
const sourceSelect = document.getElementById("sourceSelect");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const muteBtn = document.getElementById("muteBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const originalFeed = document.getElementById("originalFeed");
const translatedFeed = document.getElementById("translatedFeed");
const errorBox = document.getElementById("errorBox");
const meter = document.getElementById("meter");
const targetTag = document.getElementById("targetTag") || document.getElementById("outTag");
const debugLine = document.getElementById("debugLine");
let socket = null;
let isMuted = false;
let reconnectTimer = null;

function websocketUrl() {
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${window.location.host}/ws/translator/`;
}

function connectSocket() {
  socket = new WebSocket(websocketUrl());
  socket.addEventListener("open", () => {
    if (reconnectTimer) clearTimeout(reconnectTimer);
  });
  socket.addEventListener("message", event => {
    let data;
    try { data = JSON.parse(event.data); } catch (_) { return; }
    handleMessage(data);
  });
  socket.addEventListener("close", event => {
    updateStatus(false);
    if (event.code !== 4401) reconnectTimer = setTimeout(connectSocket, 2000);
  });
  socket.addEventListener("error", () => showError("WebSocket connection failed."));
}

function send(action, payload = {}) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    showError("The live connection is not ready. Please try again.");
    return false;
  }
  socket.send(JSON.stringify({ action, ...payload }));
  return true;
}

fetch("/languages/")
  .then(r => {
    if (!r.ok) throw new Error("Language request failed");
    return r.json();
  })
  .then(langs => {
    const entries = Object.entries(langs).sort((a, b) => a[0].localeCompare(b[0]));
    if (sourceLangSelect) {
      const auto = document.createElement("option");
      auto.value = "auto";
      auto.textContent = "Auto detect";
      sourceLangSelect.appendChild(auto);
    }
    for (const [name, code] of entries) {
      const label = name.charAt(0).toUpperCase() + name.slice(1);
      if (targetLangSelect) {
        const opt = new Option(label, code, code === "en", code === "en");
        targetLangSelect.appendChild(opt);
      }
      if (sourceLangSelect) sourceLangSelect.appendChild(new Option(label, code));
    }
  })
  .catch(() => showError("Could not load the language list."));

startBtn?.addEventListener("click", () => {
  if (send("start_translation", {
    source_lang: sourceLangSelect?.value || "auto",
    target_lang: targetLangSelect?.value || "en",
    source: sourceSelect?.value || "system",
  })) {
    startBtn.disabled = true;
    statusText.textContent = "Starting...";
  }
});

stopBtn?.addEventListener("click", () => send("stop_translation"));

muteBtn?.addEventListener("click", () => {
  isMuted = !isMuted;
  send("toggle_mute", { mute: isMuted });
  muteBtn.textContent = isMuted ? "🔇 Output Sound: OFF" : "🔊 Output Sound: ON";
  muteBtn.classList.toggle("btn-danger", isMuted);
});

targetLangSelect?.addEventListener("change", () => {
  send("change_target_language", { target_lang: targetLangSelect.value });
  if (targetTag) targetTag.textContent = `target · ${targetLangSelect.options[targetLangSelect.selectedIndex]?.text || targetLangSelect.value}`;
});

sourceSelect?.addEventListener("change", () => {
  if (muteBtn) muteBtn.style.display = sourceSelect.value === "mic" ? "none" : "flex";
});

function handleMessage(data) {
  if (data.type === "status") updateStatus(Boolean(data.running));
  else if (data.type === "error") showError(data.message || "An unknown error occurred.");
  else if (data.type === "info") showError(data.message || "Updated.", 3000);
  else if (data.type === "debug") updateDebug(data);
  else if (data.type === "translation_result") {
    const sourceTag = data.source === "mic" ? "🎙 mic" : "🔊 system";
    addEntry(originalFeed, data.original, `${data.timestamp} · ${sourceTag} · detected: ${data.detected_lang}`);
    addEntry(translatedFeed, data.translated, `${data.timestamp} · ${sourceTag} · target: ${data.target_lang}`, data.translated, data.target_lang);
  }
}

function updateStatus(running) {
  if (startBtn) { startBtn.disabled = running; startBtn.style.display = running ? "none" : "flex"; }
  if (stopBtn) { stopBtn.disabled = !running; stopBtn.style.display = running ? "flex" : "none"; }
  if (sourceSelect) sourceSelect.disabled = running;
  statusDot?.classList.toggle("active", running);
  statusDot?.classList.toggle("status-on", running);
  if (statusText) statusText.textContent = running ? "Listening..." : "System Idle";
  meter?.classList.toggle("live", running);
}

function updateDebug(data) {
  if (!debugLine) return;
  const state = data.silent ? "SILENT — skipped" : (data.note || "captured and processing");
  debugLine.textContent = `${data.timestamp} · ${data.source} · signal ${data.level} · ${state}`;
}

function addEntry(feed, text, meta, speakText, speakLang) {
  if (!feed) return;
  const placeholder = feed.querySelector("p[style*='italic']");
  if (placeholder) placeholder.remove();
  const entry = document.createElement("div");
  entry.className = "entry";
  const metaEl = document.createElement("div");
  metaEl.className = "meta";
  metaEl.textContent = meta;
  const textEl = document.createElement("div");
  textEl.textContent = text;
  entry.append(metaEl, textEl);
  if (speakText) {
    const button = document.createElement("button");
    button.className = "speak-btn";
    button.type = "button";
    button.textContent = "🔊 Speak";
    button.addEventListener("click", () => playTTS(speakText, speakLang));
    entry.appendChild(button);
  }
  feed.appendChild(entry);
  feed.scrollTop = feed.scrollHeight;
}

function csrfToken() {
  const value = document.cookie.split("; ").find(row => row.startsWith("csrftoken="));
  return value ? decodeURIComponent(value.split("=")[1]) : "";
}

function playTTS(text, lang) {
  fetch("/speak/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
    body: JSON.stringify({ text, lang }),
  })
    .then(async response => {
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || "Could not generate speech.");
      }
      return response.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.addEventListener("ended", () => URL.revokeObjectURL(url));
      return audio.play();
    })
    .catch(error => showError(error.message));
}

function showError(message, duration = 6000) {
  if (!errorBox) { console.error(message); return; }
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
  errorBox.style.display = "block";
  window.setTimeout(() => {
    errorBox.classList.add("hidden");
    errorBox.style.display = "none";
  }, duration);
}

connectSocket();
