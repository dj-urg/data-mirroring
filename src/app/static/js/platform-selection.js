// Create a Trusted Types policy using DOMPurify if supported
let ttPolicy = null;
if (window.trustedTypes) {
    ttPolicy = window.trustedTypes.createPolicy('default', {
        createHTML: (input) => DOMPurify.sanitize(input)
    });
} else {
    console.warn("Trusted Types are not supported in this browser. Falling back to direct DOMPurify usage.");
}

document.addEventListener('DOMContentLoaded', function () {
    // Add event listeners for the radio buttons
    document.getElementById('youtubeLabel').addEventListener('click', function () {
        showDescription('youtube');
    });

    document.getElementById('instagramLabel').addEventListener('click', function () {
        showDescription('instagram');
    });

    document.getElementById('tiktokLabel').addEventListener('click', function () {
        showDescription('tiktok');
    });

    document.getElementById('netflixLabel').addEventListener('click', function () {
        showDescription('netflix');
    });

    // Add event listener for the "Continue" button
    document.getElementById('continueButton').addEventListener('click', goToDashboard);
});

function showDescription(platform) {
    // Validate platform input to prevent XSS
    const allowedPlatforms = ["youtube", "instagram", "tiktok", "netflix"];
    if (!allowedPlatforms.includes(platform)) {
        console.error("Invalid platform:", platform);
        return;
    }

    const descriptions = {
        youtube: "More information on how to request your YouTube data can be found <a href='https://support.google.com/youtube/answer/9315727?hl=en' target='_blank'>here</a>.",
        instagram: "More information on how to request your Instagram data can be found <a href='https://help.instagram.com/181231772500920?helpref=faq_content' target='_blank'>here</a>.",
        tiktok: "More information on how to request your TikTok data can be found <a href='https://support.tiktok.com/en/account-and-privacy/personalized-ads-and-data/requesting-your-data' target='_blank'>here</a>.",
        netflix: "More information on how to request your Netflix data can be found <a href='https://help.netflix.com/en/node/101917' target='_blank'>here</a>."
    };

    const platformDescription = document.getElementById("platformDescription");
    const descriptionText = descriptions[platform];

    // Sanitize the hardcoded description (defense in depth)
    // Use Trusted Types if available, otherwise fallback to DOMPurify
    if (ttPolicy) {
        platformDescription.innerHTML = ttPolicy.createHTML(descriptionText);
    } else {
        platformDescription.innerHTML = DOMPurify.sanitize(descriptionText);
    }

    platformDescription.style.display = "block";

    // Reset styles
    document.getElementById("youtubeLabel").classList.remove("selected");
    document.getElementById("instagramLabel").classList.remove("selected");
    document.getElementById("tiktokLabel").classList.remove("selected");
    document.getElementById("netflixLabel").classList.remove("selected");

    // Highlight selected platform
    document.getElementById(platform + "Label").classList.add("selected");
}

function goToDashboard() {
    const platform = document.querySelector('input[name="platform"]:checked');

    if (platform) {
        const allowedPlatforms = ["youtube", "instagram", "tiktok", "netflix"];
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