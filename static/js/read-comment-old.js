let currentComment = "";
let username = "";

let audioContext;
let audioSource;
let analyzer;

const startButton = document.getElementById("startButton");

const audio = document.getElementById("player");

const musicWave = document.getElementById('musicWave');

const ctxMusicWave = musicWave.getContext('2d');

const formListCommentElm = document.getElementById('form-list-comment');

const commentBox = document.getElementById("comment");

// const urlServer = 'https://livestreamvoice.com';
const urlServer = '';

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
    formListCommentElm.style.display='block';
}
function disableFormListComment(){
    formListCommentElm.style.display='none';
}
function clearUsernameInput(){
    usernameElm.value = '';
}
function pauseAudio(){
    try{
        audio.pause();
    }
    catch(e){
        console.log(e);
    }
}
function clearListComment(){
    commentBox.innerText = '';
}

function resetTab(){
    pauseAudio();
    clearUsernameInput();
    startButtonEnable();
    disableFormListComment();
    clearListComment();
}
async function startClient() {
    flagRead = true;

    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioSource = audioContext.createMediaElementSource(audio);
        analyzer = audioContext.createAnalyser();

        audioSource.connect(analyzer);
        analyzer.connect(audioContext.destination);

        analyzer.fftSize = 256;
    }
    username = usernameElm.value.trim();
    username = platform == PLATFORM_TIKTOK ? username.toLowerCase() : username;

    if (!username) {
        showError(`Vui lòng nhập ${typeUsername.get(platform)}`);
        // startButton.innerHTML = `<i class="fas fa-rocket"></i>Start`;
        // startButton.disabled = false;
        // startButton.classList.remove("opacity-50", "cursor-not-allowed");
        return;
    }

    if(platform == PLATFORM_TIKTOK && !isValidUsername(username)){
        showError("Username không đúng định dạng");
        return;
    }

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
        // showError("Không thể kết nối tới server!");
        showError("Username/Link không đúng định dạng");
        startButtonEnable();
        return;
    }

    // Gửi request bắt đầu
    await fetch(`${urlServer}`+`/${platform}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username })
    });

    // Xử lý audio "dọn đường" cho mobile
    //const audio = document.getElementById("player");
    try {
        audio.src = ""; // Làm sạch
        await audio.play();
        audio.pause();
        audio.currentTime = 0;
        console.log("Audio unlocked bởi người dùng.");
    } catch (err) {
        console.log(err);
        // console.warn("Trình duyệt không cho phép phát audio tự động:", err);
    }
    enableFormListComment();
    startButtonReading();
    // Gọi lần đầu
    fetchComment();
}

function copyStreamSourceOBS(){
    const host = window.location.host;
    const username = document.getElementById("username").value.trim();

    navigator.clipboard.writeText(host+`/${platform}/widget/${platform == PLATFORM_TIKTOK ? username : base64UrlEncode(username)}`)
      .then(() => {
        showSuccess("Đã copy vào clipboard!");
      })
      .catch(err => {
        console.error("Lỗi khi copy vào clipboard:", err);
      });
}

function waitForAudioLoad(audio) {
    return new Promise((resolve, reject) => {
        audio.oncanplaythrough = resolve;
        audio.onerror = reject;
    });
}

async function fetchComment() {
    if(!flagRead){
        resetTab();
        return;
    }
    try {
        /*const enableReply = document.getElementById('enableReply');

        const res = await fetch(`/tiktok/comment/${username}?reply=${enableReply.checked}`);*/

        const formData = new FormData();

        if (document.getElementById("enableReply").checked) {
            formData.append("reply", "1");
        }
        if (document.getElementById("enableLike").checked) {
            formData.append("like", "1");
        }
        if (document.getElementById("enableCmt").checked) {
            formData.append("cmt", "1");
        }
        if (document.getElementById("enableGift").checked) {
            formData.append("gift", "1");
        }

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

            commentBox.innerText += currentComment + '\n';
            commentBox.scrollTop = commentBox.scrollHeight;

            //const audio = document.getElementById("player");
            audio.src = `${urlServer}/${platform}/audio/${platform == PLATFORM_TIKTOK ? username : base64UrlEncode(username)}?t=${Date.now()}`;
            //audio.load();
            // audio.playbackRate = 1.5;
            //await waitForAudioLoad(audio);

            audio.onended = () => {
                fetchComment();
            };

            // create music wave

            function resizeCanvas() {
                musicWave.width = musicWave.offsetWidth;
                musicWave.height = musicWave.offsetHeight;
            }

            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);

            const bufferLength = analyzer.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            function draw() {
                requestAnimationFrame(draw);

                analyzer.getByteFrequencyData(dataArray);

                ctxMusicWave.clearRect(0, 0, musicWave.width, musicWave.height);

                const barWidth = (musicWave.width / bufferLength) * 2.5;
                let barHeight;
                let x = 0;

                for (let i = 0; i < bufferLength; i++) {
                    barHeight = dataArray[i];
                    // ctxMusicWave.fillStyle = `rgb(${barHeight + 100},50,200)`;
                    ctxMusicWave.fillStyle = `rgb(0,${barHeight + 50},255)`;
                    ctxMusicWave.fillRect(x, musicWave.height - barHeight / 1.75, barWidth, barHeight / 1.75);
                    x += barWidth + 1;
                }
            }
            audio.onplay = () => {
                if (audioContext.state === 'suspended') {
                    audioContext.resume();
                }
                draw();
            };
            // end music wave
            await audio.play();
        } else {
            setTimeout(fetchComment, 1000);
        }
    } catch (err) {
        showError("Lỗi khi fetch hoặc phát audio!");
        setTimeout(fetchComment, 1000);
    }
}