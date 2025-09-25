const PLATFORM_TIKTOK = 'tiktok';
const PLATFORM_FACEBOOK = 'facebook';
const PLATFORM_YOUTUBE = 'youtube';

let flagRead = true;

let platform = PLATFORM_TIKTOK;
const list = document.querySelectorAll(".list");
const tabContents = document.querySelectorAll(".tab-content");

const textBannerElm = document.getElementById('text-type-platform');
const labelUsernameElm = document.getElementById('label-username');
const usernameElm = document.getElementById('username');
const listOptionReadComment = document.getElementsByClassName('option-read-comment');

function activeLink() {
    // Remove active class from all items
    list.forEach((item) => item.classList.remove("active"));
    // tabContents.forEach((content) => content.classList.remove("active"));
    //
    // // Add active class to clicked item
    this.classList.add("active");

    // Show corresponding tab content
    // const platform = this.getAttribute("data-platform");
    // document.getElementById(platform).classList.add("active");

    if(platform !== this.getAttribute("data-platform")){
        flagRead = false;
    }

    platform = this.getAttribute("data-platform");

    setupValueLabel(platform);
}

list.forEach((item) => item.addEventListener("click", activeLink));


function setupValueLabel(platform){
    textBannerElm.innerText = platform;
    let textLabelUsername = '';
    let textPlaceholderUsername = '';
    if(platform === PLATFORM_TIKTOK){
        textLabelUsername = 'Nhập TikTok username (không có @):';
        textPlaceholderUsername = 'ví dụ: nguyenvana';
    }
    else if(platform === PLATFORM_FACEBOOK){
        textLabelUsername = 'Nhập link video livestream Facebook:';
        textPlaceholderUsername = 'ví dụ: https://fb.com/lqmb/videos/634682809019140';
    }
    else if(platform === PLATFORM_YOUTUBE){
        textLabelUsername = 'Nhập link video livestream Youtube:';
        textPlaceholderUsername = 'ví dụ: https://youtube.com/watch?v=CUyoRAP9te0&ab_channel=MixiGaming'
    }
    labelUsernameElm.innerText = textLabelUsername;
    usernameElm.placeholder = textPlaceholderUsername;

    Array.from(listOptionReadComment).forEach(el => {
        const allowStr = el.getAttribute('allow-platform');
        if (!allowStr) return;

        const allowArr = JSON.parse(allowStr);

        if (allowArr.includes(platform)) {
            el.style.display = 'flex';
        } else {
            el.style.display = 'none';
        }
    });

    if(!flagRead){
        usernameElm.value = '';
        resetTab();
    }
}