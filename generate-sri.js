const axios = require('axios');
const crypto = require('crypto');
const fs = require('fs');

// List of resources to generate SRI hashes for
const resources = [
    {
        name: 'Google Fonts',
        url: 'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap',
        type: 'link',
    },
    {
        name: 'Font Awesome',
        url: 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',
        type: 'link',
    }
];

async function generateSRI() {
    for (const resource of resources) {
        try {
            const response = await axios.get(resource.url);
            const hash = crypto.createHash('sha384').update(response.data).digest('base64');
            console.log(`${resource.name} (${resource.type}):`);
            console.log(`<${resource.type} href="${resource.url}" integrity="sha384-${hash}" crossorigin="anonymous">`);
            console.log('---');
        } catch (err) {
            console.error(`Failed to fetch ${resource.url}: ${err.message}`);
        }
    }
}

generateSRI();