const fs = require('fs');
const crypto = require('crypto');

const files = [
    './app/static/js/enter_code.js',
    './app/static/js/instagram_dashboard.js',
    './app/static/js/platform-selection.js',
    './app/static/js/plotly.min.js',
    './app/static/js/tiktok_dashboard.js',
    './app/static/js/youtube_dashboard.js',
];

files.forEach((file) => {
    try {
        const content = fs.readFileSync(file, 'utf-8');
        const hash = crypto.createHash('sha384').update(content).digest('base64');
        console.log(`${file}:`);
        console.log(`<script src="${file.replace('./static', '/static')}" integrity="sha384-${hash}" crossorigin="anonymous"></script>`);
    } catch (error) {
        console.error(`Error processing ${file}:`, error.message);
    }
});