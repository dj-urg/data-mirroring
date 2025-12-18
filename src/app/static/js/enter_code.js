document.addEventListener("DOMContentLoaded", function () {
    // Apply styles to the body
    document.body.style.fontFamily = "'Helvetica', Arial, sans-serif";
    document.body.style.backgroundColor = "#f4f4f4"; // Light background
    document.body.style.display = "flex";
    document.body.style.justifyContent = "center";
    document.body.style.alignItems = "center";
    document.body.style.height = "100vh"; // Full height
    document.body.style.margin = "0";

    // Apply styles to the container
    const container = document.querySelector(".container");
    if (container) {
        container.style.backgroundColor = "white"; // White background for form
        container.style.padding = "20px";
        container.style.borderRadius = "8px";
        container.style.boxShadow = "0 4px 10px rgba(0, 0, 0, 0.1)"; // Subtle shadow
        container.style.textAlign = "center";
        container.style.maxWidth = "400px";
        container.style.width = "100%";
    }

    // Apply styles to the h1
    const h1s = document.querySelectorAll("h1");
    h1s.forEach((h1) => {
        h1.style.color = "#2C3E50";
        h1.style.marginBottom = "20px";
    });

    // Apply styles to the input[type="text"]
    const inputText = document.querySelector('input[type="text"]');
    if (inputText) {
        inputText.style.width = "100%";
        inputText.style.padding = "10px";
        inputText.style.margin = "10px 0";
        inputText.style.border = "1px solid #BDC3C7";
        inputText.style.borderRadius = "4px";
    }

    // Apply styles to buttons
    const buttons = document.querySelectorAll("button");
    buttons.forEach((button) => {
        button.style.backgroundColor = "#3498DB";
        button.style.color = "white";
        button.style.padding = "10px";
        button.style.border = "none";
        button.style.borderRadius = "4px";
        button.style.cursor = "pointer";
        button.style.width = "100%";

        // Add hover effect to buttons
        button.addEventListener("mouseover", function () {
            button.style.backgroundColor = "#2980B9";
        });

        button.addEventListener("mouseout", function () {
            button.style.backgroundColor = "#3498DB";
        });
    });

    // Apply styles to the error message
    const errorMessage = document.querySelector(".error-message");
    if (errorMessage) {
        errorMessage.style.color = "red";
        errorMessage.style.marginTop = "10px";
    }

    // Cookie Banner Logic
    const cookieBanner = document.getElementById("cookie-banner");
    const accessCodeSection = document.getElementById("access-code-section");
    const acceptCookiesButton = document.getElementById("accept-cookies");

    // Check if cookies have already been accepted
    if (localStorage.getItem("cookiesAccepted")) {
        cookieBanner.classList.add("hidden"); // Hide cookie banner
        accessCodeSection.classList.remove("hidden"); // Show access to the code section
    } else {
        cookieBanner.classList.remove("hidden"); // Show cookie banner
        accessCodeSection.classList.add("hidden"); // Hide access to the code section
    }

    // When "Accept" is clicked, save consent and show the access code section
    acceptCookiesButton.addEventListener("click", function () {
        localStorage.setItem("cookiesAccepted", "true");
        cookieBanner.classList.add("hidden"); // Hide cookie banner
        accessCodeSection.classList.remove("hidden"); // Show access to the code section
    });
});