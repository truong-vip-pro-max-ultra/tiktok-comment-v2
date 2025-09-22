let currentComment = "";
let username = "";

let audioContext;
let audioSource;
let analyzer;

const audio = document.getElementById("player");

const musicWave = document.getElementById('musicWave');
const ctxMusicWave = musicWave.getContext('2d');

async function startClient() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioSource = audioContext.createMediaElementSource(audio);
        analyzer = audioContext.createAnalyser();

        audioSource.connect(analyzer);
        analyzer.connect(audioContext.destination);

        analyzer.fftSize = 256;
    }
    const button = document.getElementById("startButton");
    username = document.getElementById("username").value.trim().toLowerCase();
    if (!username) {
        showError("Vui lòng nhập username");
        button.innerHTML = `<i class="fas fa-rocket"></i>Start`;
        button.disabled = false;
        button.classList.remove("opacity-50", "cursor-not-allowed");
        return;
    }

    try {
        button.innerText = "Đang kiểm tra...";
        button.disabled = true;
        button.classList.add("opacity-50", "cursor-not-allowed");

        const check_live = await fetch(`/tiktok/check/${username}`);
        if (check_live.status === 400) {
            button.innerHTML = `<i class="fas fa-rocket"></i>Start`;
            button.disabled = false;
            button.classList.remove("opacity-50", "cursor-not-allowed");
            showError(`${username} không đúng hoặc không livestream`);
            return;
        } else if (!check_live.ok) {
            button.innerHTML = `<i class="fas fa-rocket"></i>Start`;
            button.disabled = false;
            button.classList.remove("opacity-50", "cursor-not-allowed");
            showError("Đã xảy ra lỗi. Vui lòng thử lại!");
            return;
        } else {
            showSuccess("Start thành công");
        }
    } catch (error) {
        console.error("Lỗi khi gửi request:", error);
        showError("Không thể kết nối tới server!");
    }

    // Gửi request bắt đầu
    await fetch("/tiktok/start", {
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
        console.warn("Trình duyệt không cho phép phát audio tự động:", err);
    }


    button.innerText = "Đang Đọc...";
    button.disabled = true;
    button.classList.add("opacity-50", "cursor-not-allowed");
    // Gọi lần đầu
    fetchComment();
}

function copyStreamSourceOBS(){
    const host = window.location.host;
    const username = document.getElementById("username").value.trim();

    navigator.clipboard.writeText(host+'/tiktok/widget/'+username)
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

        const res = await fetch(`/tiktok/comment/${username}`, {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        if (data.latest_comment == "" && currentComment != "") {
             await fetch("/tiktok/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username })
            });
        }

        if (data.latest_comment && data.latest_comment !== currentComment) {
            currentComment = data.latest_comment;

            const commentBox = document.getElementById("comment");
            commentBox.innerText += currentComment + '\n';
            commentBox.scrollTop = commentBox.scrollHeight;

            //const audio = document.getElementById("player");
            audio.src = `/tiktok/audio/${username}?t=${Date.now()}`;
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
                /*for (let i = 0; i < bufferLength; i++) {
                    barHeight = dataArray[i];
                    let gradient = ctxMusicWave.createLinearGradient(
                        0,
                        musicWave.height - barHeight / 1.75,
                        0,
                        musicWave.height
                    );

                    gradient.addColorStop(0, "rgba(255, 255, 255, 1)");
                    gradient.addColorStop(1, "rgb(0,39,223)");

                    ctxMusicWave.fillStyle = gradient;
                    ctxMusicWave.fillRect(
                        x,
                        musicWave.height - barHeight / 1.75,
                        barWidth,
                        barHeight / 1.75
                    );

                    x += barWidth + 1;
                }*/

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
