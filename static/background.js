const list = document.querySelectorAll(".list");
const tabContents = document.querySelectorAll(".tab-content");

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
}

list.forEach((item) => item.addEventListener("click", activeLink));

function openProfile(platform) {
    const username = document.getElementById(`${platform}-username`).value;

    if (!username) {
        alert("Vui lòng nhập username!");
        return;
    }

    let url = "";
    switch(platform) {
        case "tiktok":
            url = `https://www.tiktok.com/${username.startsWith('@') ? username : '@' + username}`;
            break;
        case "facebook":
            url = `https://www.facebook.com/${username}`;
            break;
        case "youtube":
            url = `https://www.youtube.com/${username.startsWith('@') ? username : '@' + username}`;
            break;
    }

    window.open(url, '_blank');
}

// Allow Enter key to submit
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        const activeTab = document.querySelector('.tab-content.active').id;
        openProfile(activeTab);
    }
});