function showError(message) {
    const popup = document.getElementById("errorPopup");
    const msg = document.getElementById("errorMessage");

    msg.innerText = message;
    popup.classList.remove("hidden");

    // Tự ẩn sau 4 giây
    setTimeout(() => {
      hideError();
    }, 4000);
}
function showSuccess(message) {
    const popup = document.getElementById("successPopup");
    const msg = document.getElementById("successMessage");

    msg.innerText = message;
    popup.classList.remove("hidden");

    // Tự ẩn sau 4 giây
    setTimeout(() => {
      hideSuccess();
    }, 4000);
}


function hideError() {
    const popup = document.getElementById("errorPopup");
    popup.classList.add("hidden");
}
function hideSuccess() {
    const popup = document.getElementById("successPopup");
    popup.classList.add("hidden");
}
