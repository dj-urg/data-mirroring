# Data Mirroring 

[![Requires Python 3.8](https://img.shields.io/badge/py-v3.8-blue)](https://www.python.org/) 
[![License: MPL 2.0](https://img.shields.io/badge/license-MPL--2.0-informational)](https://github.com/dj-urg/data-mirroring?tab=License-1-ov-file#)

## 🌐 Overview

Welcome to the Data Mirroring research project, developed by Daniel Jurg, Sarah Vis, and Ike Picone at the Vrije Universiteit Brussel as part of the NUSE-Unit. 

This project aims to facilitate user reflection on social media usage through data conversion and visualization. The application transforms specific files in Data Download Packages (DDPs) provided by social media platforms like TikTok, Instagram, and YouTube into a more human-readable format.

By processing a subset of the DDPs, the application offers social media users insights into their data while ensuring the removal of potentially sensitive information before possible data donation. Uploaded data, CSVs, and generated visualizations are processed in-memory or saved as temporary files during your session and deleted after use.

While the Data Mirroring application provides initial insights into data, it is designed to export social media data in tabular format for further processing in other tools.

## ✨ Features

- **Platform Selection**: Choose between YouTube, Instagram, and TikTok for data processing.
- **File Upload**: Upload multiple JSON files for each platform.
- **Data Processing**: Generates insights and visualizations from uploaded platform data.
- **Download CSV**: After processing, you can download a CSV file of the results.

## 🛠 Configuration

Before running the application, set the required environment variables:

**Linux/macOS (Terminal)**
```bash
export SECRET_KEY=test
export ACCESS_CODE=test
export FLASK_ENV=development
```

**Windows (Command Prompt)**
```bash
set SECRET_KEY=test
set ACCESS_CODE=test
set FLASK_ENV=development
```

Or create a `.env` file and add:
```bash
SECRET_KEY=example
ACCESS_CODE=example
FLASK_ENV=development
```

## 📦 Installation

**Step 1:** Clone the repository
```bash
git clone https://github.com/dj-urg/data-mirroring.git
```

**Step 2:** Install dependencies
```bash
pip install -r requirements.txt
```

**Step 3:** Run the application
```bash
python app.py
```

## 🚀 Usage

The application listens on port 5001 by default. After running the application, it will output the specific URL and port it's using. You can change the port by setting the `PORT` environment variable before running the application.

Example:
```bash
PORT=8080 python app.py
```

## 💻 Technologies Used

- **Languages:** Python, CSS, Dockerfile, HTML, JavaScript
- **Framework:** Flask
- **Other Tools:** Docker, GitHub Actions

## 🔒 Security & Best Practices

- Use environment variables instead of hardcoding secrets.
- Follow GitHub security updates for dependencies.

## 🤝 Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit changes (`git commit -m "Add feature"`)
4. Push (`git push origin feature-branch`)
5. Open a Pull Request

## 📄 License

Mozilla Public License Version 2.0

## 🙏 Acknowledgments and Code Generation

This project leverages the power of modern AI tools to aid development. Portions of the code were generated or assisted by:

* **Claude:** Used for brainstorming, code generation, code refinement, and fixing bugs.
* **ChatGPT:** Used for brainstorming, code generation, code refinement, and fixing bugs.
* **GitHub Copilot:** Integrated into the development environment to provide real-time code suggestions and completions.

We acknowledge the contributions of these AI models in the creation of this project. While these tools aided in development, the authors have requested expert advice to ensure the code's functionality and security.

## 📧 Contact

For questions or issues, please contact daniel.jurg@vub.be
