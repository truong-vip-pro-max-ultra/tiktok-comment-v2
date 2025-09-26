let currentComment = "";
let username = "";

let audioContext;
let audioSource;
let analyzer;

const startButton = document.getElementById("startButton");
const audio = document.getElementById("player");

const musicWave = document.getElementById('musicWave');
const ctxMusicWave = musicWave ? musicWave.getContext('2d') : null;

const formListCommentElm = document.getElementById('form-list-comment');
const commentBox = document.getElementById("comment");

// const urlServer = 'https://livestreamvoice.com';
const urlServer = '';

const RATE_LS_KEY = 'ttsRate';
const RATE_MIN = 0.5;
const RATE_MAX = 3.0;

function clampRate(v) {
  const n = parseFloat(v);
  if (!Number.isFinite(n)) return 1;
  return Math.max(RATE_MIN, Math.min(RATE_MAX, n));
}

function getCurrentRate() {
  if (typeof window.lvVoiceRate === 'number') return clampRate(window.lvVoiceRate);
  const saved = localStorage.getItem(RATE_LS_KEY);
  return clampRate(saved ?? 1);
}

function applyAudioRate() {
  if (!audio) return;
  const r = getCurrentRate();
  try {
    audio.playbackRate = r;

    if ('preservesPitch' in audio) audio.preservesPitch = true;
    if ('mozPreservesPitch' in audio) audio.mozPreservesPitch = true;
    if ('webkitPreservesPitch' in audio) audio.webkitPreservesPitch = true;
  } catch (e) {
    console.warn('Cannot set playbackRate:', e);
  }
}

document.addEventListener('lv-rate-change', (e) => {
  const r = clampRate(e?.detail?.rate ?? 1);
  window.lvVoiceRate = r;
  try { localStorage.setItem(RATE_LS_KEY, r); } catch {}
  applyAudioRate();
});

(function bootstrapRateOnLoad() {
  const boot = clampRate(localStorage.getItem(RATE_LS_KEY) ?? 1);
  if (typeof window.lvVoiceRate !== 'number') {
    window.lvVoiceRate = boot;
  }
  applyAudioRate();
})();

const typeUsername = new Map();
typeUsername.set(PLATFORM_TIKTOK, 'username');
typeUsername.set(PLATFORM_FACEBOOK, 'link');
typeUsername.set(PLATFORM_YOUTUBE, 'link');

function isValidUsername(username) {
  const regex = /^[A-Za-z0-9@._-]+$/;
  return regex.test(username);
}

function startButtonEnable(){
  startButton.innerHTML = `<i class="fas fa-rocket"></i>Start`;
  startButton.disabled = false;
  startButton.classList.remove("opacity-50", "cursor-not-allowed");
}

function startButtonChecking(){
  startButton.innerText = "Đang kiểm tra...";
  startButton.disabled = true;
  startButton.classList.add("opacity-50", "cursor-not-allowed");
}

function startButtonReading(){
  startButton.innerText = "Đang Đọc...";
  startButton.disabled = true;
  startButton.classList.add("opacity-50", "cursor-not-allowed");
}

function base64UrlEncode(str) {
  let base64 = btoa(str);
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function enableFormListComment(){
  if (formListCommentElm) formListCommentElm.style.display='block';
}
function disableFormListComment(){
  if (formListCommentElm) formListCommentElm.style.display='none';
}
function clearUsernameInput(){
  if (typeof usernameElm !== 'undefined' && usernameElm) usernameElm.value = '';
}
function pauseAudio(){
  try{ audio.pause(); } catch(e){ console.log(e); }
}
function clearListComment(){
  if (commentBox) commentBox.innerText = '';
}

function resetTab(){
  pauseAudio();
  clearUsernameInput();
  startButtonEnable();
  disableFormListComment();
  clearListComment();
}

// ================================
// Audio Analyzer (nhạc nền sóng)
// ================================
function initAudioGraphIfNeeded() {
  if (audioContext) return;
  if (!audio) return;

  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  audioSource = audioContext.createMediaElementSource(audio);
  analyzer = audioContext.createAnalyser();

  audioSource.connect(analyzer);
  analyzer.connect(audioContext.destination);

  analyzer.fftSize = 256;

  applyAudioRate();
}

function drawMusicWave() {
  if (!musicWave || !ctxMusicWave || !analyzer) return;

  function resizeCanvas() {
    musicWave.width = musicWave.offsetWidth;
    musicWave.height = musicWave.offsetHeight;
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  const bufferLength = analyzer.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  (function draw() {
    requestAnimationFrame(draw);
    analyzer.getByteFrequencyData(dataArray);

    ctxMusicWave.clearRect(0, 0, musicWave.width, musicWave.height);

    const barWidth = (musicWave.width / bufferLength) * 2.5;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const barHeight = dataArray[i];
      ctxMusicWave.fillStyle = `rgb(0,${barHeight + 50},255)`;
      ctxMusicWave.fillRect(
        x,
        musicWave.height - barHeight / 1.75,
        barWidth,
        barHeight / 1.75
      );
      x += barWidth + 1;
    }
  })();
}

async function startClient() {
  flagRead = true;

  initAudioGraphIfNeeded();

  username = (usernameElm?.value || '').trim();
  username = platform == PLATFORM_TIKTOK ? username.toLowerCase() : username;

  if (!username) {
    showError(`Vui lòng nhập ${typeUsername.get(platform)}`);
    return;
  }
  if (platform == PLATFORM_TIKTOK && !isValidUsername(username)){
    showError("Username không đúng định dạng");
    return;
  }

  // Check live
  try {
    startButtonChecking();
    const check_live = await fetch(`${urlServer}/${platform}/check/${platform == PLATFORM_TIKTOK ? username : base64UrlEncode(username)}`);
    if (check_live.status === 400) {
      startButtonEnable();
      showError(`${username} không đúng hoặc không livestream`);
      return;
    } else if (!check_live.ok) {
      startButtonEnable();
      showError("Đã xảy ra lỗi. Vui lòng thử lại!");
      return;
    } else {
      showSuccess("Start thành công");
    }
  } catch (error) {
    console.error("Lỗi khi gửi request:", error);
    showError("Username/Link không đúng định dạng");
    startButtonEnable();
    return;
  }

  // Gửi request bắt đầu
  await fetch(`${urlServer}/${platform}/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username })
  });

  // "Mở khoá" audio trên mobile
  try {
    audio.src = ""; // Làm sạch
    await audio.play();
    audio.pause();
    audio.currentTime = 0;
    applyAudioRate(); // quan trọng
    console.log("Audio unlocked bởi người dùng.");
  } catch (err) {
    console.log(err);
  }

  enableFormListComment();
  startButtonReading();

  // Bắt đầu vòng fetch
  fetchComment();
}

function copyStreamSourceOBS(){
  const origin = window.location.origin;
  const name = (document.getElementById("username")?.value || '').trim();
  const idForUrl = platform == PLATFORM_TIKTOK ? name : base64UrlEncode(name);

  navigator.clipboard.writeText(`${origin}/${platform}/widget/${idForUrl}`)
    .then(() => showSuccess("Đã copy vào clipboard!"))
    .catch(err => console.error("Lỗi khi copy vào clipboard:", err));
}

function waitForAudioLoad(audioEl) {
  return new Promise((resolve, reject) => {
    audioEl.oncanplaythrough = resolve;
    audioEl.onerror = reject;
  });
}

async function fetchComment() {
  if (!flagRead) {
    resetTab();
    return;
  }

  try {
    // Build form options
    const formData = new FormData();
    if (document.getElementById("enableReply")?.checked) formData.append("reply", "1");
    if (document.getElementById("enableLike")?.checked)  formData.append("like", "1");
    if (document.getElementById("enableCmt")?.checked)   formData.append("cmt", "1");
    if (document.getElementById("enableGift")?.checked)  formData.append("gift", "1");

    const res = await fetch(`${urlServer}/${platform}/comment/${platform == PLATFORM_TIKTOK ? username : base64UrlEncode(username)}`, {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (data.latest_comment == "" && currentComment != "") {
      await fetch(`${urlServer}/${platform}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username })
      });
    }

    if (data.latest_comment && data.latest_comment !== currentComment) {
      currentComment = data.latest_comment;

      if (commentBox) {
        commentBox.innerText += currentComment + '\n';
        commentBox.scrollTop = commentBox.scrollHeight;
      }

      audio.src = `${urlServer}/${platform}/audio/${platform == PLATFORM_TIKTOK ? username : base64UrlEncode(username)}?t=${Date.now()}`;

      applyAudioRate();
      audio.onloadedmetadata = () => {
        applyAudioRate();
      };
      audio.addEventListener('play', applyAudioRate, { once: true }); // 3) ngay trước khi phát

      audio.onended = () => {
        fetchComment();
      };

      audio.onplay = () => {
        if (audioContext?.state === 'suspended') {
          audioContext.resume();
        }
        drawMusicWave();
      };

      await audio.play();
    } else {
      setTimeout(fetchComment, 1000);
    }
  } catch (err) {
    showError("Lỗi khi fetch hoặc phát audio!");
    setTimeout(fetchComment, 1000);
  }
}