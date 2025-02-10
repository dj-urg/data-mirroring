// Create a Trusted Types policy using DOMPurify
const ttPolicy = window.trustedTypes.createPolicy('default', {
    createHTML: (input) => DOMPurify.sanitize(input)
});

document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners for the radio buttons
    document.getElementById('youtubeLabel').addEventListener('click', function() {
        showDescription('youtube');
    });

    document.getElementById('instagramLabel').addEventListener('click', function() {
        showDescription('instagram');
    });

    document.getElementById('tiktokLabel').addEventListener('click', function() {
        showDescription('tiktok');
    });

    // Add event listener for the "Continue" button
    document.querySelector('input[type="button"]').addEventListener('click', function() {
        goToDashboard();
    });
});

function showDescription(platform) {
    const descriptions = {
        youtube: "More information on how to request your YouTube data can be found <a href='https://support.google.com/youtube/answer/9315727?hl=en' target='_blank'>here</a>.",
        instagram: "More information on how to request your Instagram data can be found <a href='https://help.instagram.com/181231772500920?helpref=faq_content' target='_blank'>here</a>.",
        tiktok: "More information on how to request your TikTok data can be found <a href='https://support.tiktok.com/en/account-and-privacy/personalized-ads-and-data/requesting-your-data' target='_blank'>here</a>."
    };

    const platformDescription = document.getElementById("platformDescription");
    platformDescription.innerHTML = ttPolicy.createHTML(descriptions[platform]); // Use TrustedHTML
    platformDescription.style.display = "block";

    // Reset styles
    document.getElementById("youtubeLabel").classList.remove("selected");
    document.getElementById("instagramLabel").classList.remove("selected");
    document.getElementById("tiktokLabel").classList.remove("selected");

    // Highlight selected platform
    document.getElementById(platform + "Label").classList.add("selected");
}

function goToDashboard() {
    const platform = document.querySelector('input[name="platform"]:checked');

    if (platform) {
        const allowedPlatforms = ["youtube", "instagram", "tiktok"];
        const selectedPlatform = platform.value.trim().toLowerCase();

        if (allowedPlatforms.includes(selectedPlatform)) {
            window.location.href = "/dashboard/" + encodeURIComponent(selectedPlatform);
        } else {
            alert("Invalid platform selection.");
        }
    } else {
        alert("Please select a platform before proceeding.");
    }
}