# Data Mirroring

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License: MPL 2.0](https://img.shields.io/badge/license-MPL--2.0-informational)](LICENSE)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![DOI: 10.5281/zenodo.15102049](https://zenodo.org/badge/DOI/10.5281/zenodo.15102049.svg)](https://doi.org/10.5281/zenodo.15102049)
[![Vrije Universiteit Brussel](https://img.shields.io/badge/University-Vrije_Universiteit_Brussel-0089CF)](https://www.vub.be/nl)
[![imec-SMIT](https://img.shields.io/badge/Research-imec--SMIT-red)](https://smit.research.vub.be/en)

> A privacy-first web application for transforming social media Data Download Packages (DDPs) into human-readable formats with visualizations and insights.

<p align="center">
  <img width="32%" alt="YouTube Dashboard" src="https://github.com/user-attachments/assets/0aec8e38-c616-447d-a58c-1e19f1c8d745" />
  <img width="32%" alt="Data Visualization" src="https://github.com/user-attachments/assets/636c4760-9b73-4e51-90d4-45eb1f07a638" />
  <img width="32%" alt="Platform Selection" src="https://github.com/user-attachments/assets/e4d3a169-d63d-4cba-99b1-a515d864b751" />
</p>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Supported Platforms](#-supported-platforms)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [Usage](#-usage)
- [Docker Deployment](#-docker-deployment)
- [Architecture](#-architecture)
- [Security & Privacy](#-security--privacy)
- [Contributing](#-contributing)
- [License](#-license)
- [Citation](#-citation)
- [Contact](#-contact)

---

## 🌐 Overview

**Data Mirroring** is a research project developed by Daniel Jurg, Sarah Vis, and Ike Picone at **imec-SMIT, Vrije Universiteit Brussel** as part of the NUSE-Unit.

This Flask-based web application empowers social media users to:
- **Understand their digital footprint** by converting complex JSON files from Data Download Packages (DDPs) into readable CSV formats
- **Visualize their activity patterns** through interactive charts and heatmaps
- **Prepare data for donation** by removing sensitive information while maintaining analytical value
- **Export processed data** for further analysis in external tools

### Key Principles

🔒 **Privacy-First Design**: All data is processed in-memory or as temporary files during your session and automatically deleted afterward. No user data is retained on the server.

🎯 **User Empowerment**: Designed to help users reflect on their social media usage patterns and make informed decisions about their digital presence.

📊 **Research-Oriented**: Built to facilitate data donation for academic research while respecting user privacy and GDPR compliance.

---

## ✨ Features

### Core Functionality
- 📤 **Multi-File Upload**: Process multiple JSON files simultaneously from your DDP
- 🔄 **Data Transformation**: Convert complex nested JSON structures into clean, tabular CSV format
- 📊 **Interactive Visualizations**: Generate charts, heatmaps, and timeline visualizations
- 💾 **Export Options**: Download processed data as CSV or Excel files for further analysis
- 🧹 **Data Sanitization**: Automatically remove sensitive information before export

### Platform-Specific Processing
- **YouTube**: Watch history, search history, comments, and engagement patterns
- **Instagram**: Posts, stories, messages, and interaction analytics
- **TikTok**: Video history, likes, comments, and browsing behavior
- **Netflix**: Viewing history and watch patterns

### Security & Privacy Features
- 🔐 **HTTPS Enforcement**: All traffic encrypted in production
- 🛡️ **CSRF Protection**: Secure form submissions with token validation
- 🚦 **Rate Limiting**: Protection against abuse and DoS attacks
- 🔑 **Access Control**: Authentication required for all sensitive routes
- 🗑️ **Automatic Cleanup**: Session-based temporary file management
- 📝 **Security Headers**: CSP, HSTS, X-Frame-Options, and more

### Technical Features
- ⚡ **In-Memory Processing**: Fast data processing without persistent storage
- 🐳 **Docker Support**: Containerized deployment for consistency
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🌍 **GDPR Compliant**: No data retention, full transparency

---

## 🎯 Supported Platforms

| Platform | Data Types Supported | File Format |
|----------|---------------------|-------------|
| **YouTube** | Watch history, search history, comments, likes | JSON |
| **Instagram** | Posts, stories, messages, followers, likes | JSON |
| **TikTok** | Video history, likes, comments, browsing data | JSON |
| **Netflix** | Viewing history, watch patterns | CSV |

> **Note**: Each platform's DDP structure may vary. The application is designed to handle the most common formats as of 2025.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.13** or higher (Python 3.8+ may work but is not officially supported)
- **pip** package manager
- **Docker** (optional, for containerized deployment)
- **Git** for cloning the repository

### Installation

#### Option 1: Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dj-urg/data-mirroring.git
   cd data-mirroring
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

#### Option 2: Docker Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dj-urg/data-mirroring.git
   cd data-mirroring
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

### Configuration

Before running the application, you must configure environment variables. Create a `.env` file in the project root:

```bash
# Required: Secret key for session management (use a strong random string)
SECRET_KEY=your-secret-key-here

# Required: Access code for authentication
ACCESS_CODE=your-access-code-here

# Optional: Environment mode (development or production)
FLASK_ENV=development

# Optional: Port number (default: 5001)
PORT=5001

# Optional: CORS allowed origins (comma-separated)
CORS_ALLOWED_ORIGINS=https://data-mirror-72f6ffc87917.herokuapp.com
```

**Security Note**: Never commit your `.env` file to version control. Use strong, randomly generated values for `SECRET_KEY` and `ACCESS_CODE` in production.

<details>
<summary>Alternative: Environment Variables (Click to expand)</summary>

**Linux/macOS**
```bash
export SECRET_KEY=your-secret-key-here
export ACCESS_CODE=your-access-code-here
export FLASK_ENV=development
```

**Windows (Command Prompt)**
```cmd
set SECRET_KEY=your-secret-key-here
set ACCESS_CODE=your-access-code-here
set FLASK_ENV=development
```

**Windows (PowerShell)**
```powershell
$env:SECRET_KEY="your-secret-key-here"
$env:ACCESS_CODE="your-access-code-here"
$env:FLASK_ENV="development"
```
</details>

### Running the Application

#### Local Development

```bash
python src/app.py
```

The application will start on `http://localhost:5001` by default.

#### Production with Gunicorn

```bash
gunicorn --bind 0.0.0.0:5001 'src.app:create_app()'
```

#### Custom Port

```bash
PORT=8080 python src/app.py
```

---

## 💡 Usage

### Step-by-Step Guide

1. **Access the Application**
   - Open your browser and navigate to `http://localhost:5001`
   - Enter the access code you configured in the `.env` file

2. **Select Platform**
   - Choose the social media platform (YouTube, Instagram, TikTok, or Netflix)

3. **Upload Data Files**
   - Click "Choose Files" and select JSON files from your DDP
   - You can upload multiple files at once (max 16MB per file)

4. **View Results**
   - The application will process your data and display:
     - Summary statistics
     - Interactive visualizations
     - Data preview tables

5. **Export Data**
   - Download processed data as CSV or Excel
   - All sensitive information is automatically removed

### Obtaining Your Data Download Package

Each platform has a different process for requesting your data:

- **YouTube/Google**: [Google Takeout](https://takeout.google.com/)
- **Instagram**: Settings → Security → Download Data
- **TikTok**: Settings → Privacy → Download your data
- **Netflix**: Account → Download your personal information

> **Processing Time**: DDPs can take several days to be prepared by the platform. File sizes vary from a few MB to several GB depending on your activity.

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start the application
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop the application
docker-compose down
```

### Using Docker Directly

```bash
# Build the image
docker build -t data-mirroring .

# Run the container
docker run -p 5001:5001 \
  -e SECRET_KEY=your-secret-key \
  -e ACCESS_CODE=your-access-code \
  -e FLASK_ENV=production \
  data-mirroring
```

### Heroku Deployment

The application is configured for Heroku deployment with the included `Procfile`:

```bash
# Login to Heroku
heroku login

# Create a new app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ACCESS_CODE=your-access-code
heroku config:set FLASK_ENV=production

# Deploy
git push heroku master
```

---

## 🏗️ Architecture

### Project Structure

```
data-mirroring/
├── src/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── routes.py            # Application routes
│   │   ├── handlers/            # Platform-specific processors
│   │   │   ├── youtube.py
│   │   │   ├── instagram.py
│   │   │   ├── tiktok.py
│   │   │   └── netflix.py
│   │   ├── utils/               # Utility modules
│   │   │   ├── config.py        # Configuration management
│   │   │   ├── security.py      # Security middleware
│   │   │   ├── file_manager.py  # Temporary file handling
│   │   │   ├── file_validation.py
│   │   │   └── logging_config.py
│   │   ├── static/              # CSS, JS, images
│   │   └── templates/           # HTML templates
│   └── app.py                   # Application entry point
├── jupyter/                     # Data analysis notebooks
├── logs/                        # Application logs
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose setup
├── requirements.txt             # Python dependencies
├── Procfile                     # Heroku deployment config
├── LICENSE                      # MPL 2.0 license
├── SECURITY.md                  # Security documentation
└── README.md                    # This file
```

### Technology Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.13, Flask 3.1.2 |
| **Data Processing** | Pandas, NumPy |
| **Visualization** | Matplotlib, Seaborn |
| **Security** | Flask-WTF (CSRF), Flask-Limiter, python-magic |
| **Session Management** | Flask-Session |
| **Server** | Gunicorn (production), Flask dev server (development) |
| **Containerization** | Docker, Docker Compose |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Deployment** | Heroku, Docker |

### Key Components

- **Flask Application Factory**: Modular app initialization with blueprint registration
- **Platform Handlers**: Specialized processors for each social media platform's data format
- **Temporary File Manager**: Session-based file lifecycle management with automatic cleanup
- **Security Middleware**: HTTPS enforcement, CSP headers, CSRF protection, rate limiting
- **File Validation**: Magic number verification, size limits, extension checking

---

## 🔒 Security & Privacy

This application is designed with **security and privacy as top priorities**. For detailed information, see [SECURITY.md](SECURITY.md).

### Privacy Guarantees

✅ **No Data Retention**: All uploaded files and processed data are deleted after your session ends
✅ **In-Memory Processing**: Data is processed in RAM whenever possible
✅ **Temporary Files Only**: Any files written to disk are stored in session-specific temporary directories
✅ **Automatic Cleanup**: Files are automatically deleted on session end, server restart, and periodically
✅ **No Analytics**: No tracking, cookies, or third-party analytics
✅ **GDPR Compliant**: Full compliance with EU data protection regulations

### Security Features

🔐 **HTTPS Enforcement**: All HTTP traffic redirected to HTTPS in production
🛡️ **Content Security Policy**: Dynamic CSP with nonces to prevent XSS attacks
🔑 **CSRF Protection**: Token-based protection for all form submissions
🚦 **Rate Limiting**: Per-user rate limits to prevent abuse
🔒 **Secure Headers**: HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy
👤 **Authentication**: Access code required for all routes
📝 **Input Validation**: Strict file validation with magic number verification
🧹 **File Sanitization**: Secure filename handling and path traversal prevention

### Security Testing

The application has been tested using:
- [ImmuniWeb Security Test](https://www.immuniweb.com/websec)
- GitHub Dependabot for dependency vulnerability scanning
- GitHub Code Scanning for security issues

### Reporting Security Issues

If you discover a security vulnerability, please email **daniel.jurg@vub.be** directly. Do not open a public issue.

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### How to Contribute

1. **Fork the repository**
   ```bash
   git clone https://github.com/dj-urg/data-mirroring.git
   cd data-mirroring
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests if applicable
   - Update documentation as needed

4. **Test your changes**
   ```bash
   python -m pytest  # If tests are available
   python src/app.py  # Manual testing
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add: Brief description of your changes"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Wait for review and address feedback

### Contribution Guidelines

- **Code Quality**: Follow PEP 8 style guidelines for Python code
- **Security**: Never commit sensitive data (API keys, passwords, etc.)
- **Documentation**: Update README.md and inline comments as needed
- **Testing**: Ensure your changes don't break existing functionality
- **Commits**: Use clear, descriptive commit messages

### Areas for Contribution

- 🐛 Bug fixes and error handling improvements
- ✨ Support for additional social media platforms
- 📊 New visualization types
- 🌍 Internationalization and translations
- 📝 Documentation improvements
- 🧪 Test coverage expansion
- ♿ Accessibility enhancements

---

## 📄 License

This project is licensed under the **Mozilla Public License Version 2.0** (MPL-2.0).

**Copyright © 2025 Daniel Jurg, Sarah Vis, and Ike Picone**

This Source Code Form, except for third-party libraries included and listed in the [LICENSE-3DPARTY.md](LICENSE-3DPARTY.md) file, is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

See [LICENSE](LICENSE) for the full license text.

---

## 📚 Citation

If you use this software in your research, please cite:

```bibtex
@software{jurg_data_mirroring_2025,
  author = {Jurg, Daniel and Vis, Sarah and Picone, Ike},
  title = {Data Mirroring: Privacy-First Social Media Data Processing},
  year = {2025},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.15102049},
  url = {https://github.com/dj-urg/data-mirroring}
}
```

**DOI**: [10.5281/zenodo.15102049](https://doi.org/10.5281/zenodo.15102049)

---

## 🙏 Acknowledgments

### Research Institution

This project was developed at:
- **imec-SMIT** (Studies in Media, Innovation and Technology)
- **Vrije Universiteit Brussel** (VUB)
- **NUSE-Unit** (News Use and Social Engagement)

### AI-Assisted Development

This project leverages modern AI tools to aid development. Portions of the code were generated or assisted by:
- **Claude**: Brainstorming, code generation, refinement, and debugging
- **ChatGPT**: Code generation, refinement, and problem-solving
- **GitHub Copilot**: Real-time code suggestions and completions

While these tools aided in development, the authors have consulted with experts to ensure the code's functionality, security, and compliance with best practices.

### Third-Party Libraries

This project uses several open-source libraries. See [LICENSE-3DPARTY.md](LICENSE-3DPARTY.md) for details.

---

## 📧 Contact & Support

### Maintainers

- **Daniel Jurg** - Lead Developer - [daniel.jurg@vub.be](mailto:daniel.jurg@vub.be)
- **Sarah Vis** - Researcher
- **Ike Picone** - Principal Investigator

### Getting Help

- 📧 **Email**: daniel.jurg@vub.be
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/dj-urg/data-mirroring/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/dj-urg/data-mirroring/discussions)
- 🔒 **Security Issues**: Email daniel.jurg@vub.be directly (do not open public issues)

### Links

- 🌐 **Live Demo**: [https://data-mirror-72f6ffc87917.herokuapp.com](https://data-mirror-72f6ffc87917.herokuapp.com)
- 📖 **Documentation**: [SECURITY.md](SECURITY.md)
- 🏛️ **Institution**: [imec-SMIT](https://smit.research.vub.be/en)
- 🎓 **University**: [Vrije Universiteit Brussel](https://www.vub.be/nl)

---

<p align="center">
  Made with ❤️ by the imec-SMIT research team at VUB
</p>

<p align="center">
  <a href="https://www.vub.be/nl">
    <img src="https://img.shields.io/badge/University-Vrije_Universiteit_Brussel-0089CF" alt="VUB">
  </a>
  <a href="https://smit.research.vub.be/en">
    <img src="https://img.shields.io/badge/Research-imec--SMIT-red" alt="imec-SMIT">
  </a>
</p>
