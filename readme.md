# Data Mirror 3.0

Data Mirror 3.0 is a Flask-based web application that allows users to upload and process data from platforms such as YouTube and Instagram. It generates visual insights and provides downloadable CSV files based on the uploaded JSON data. The app includes a dashboard for each supported platform, enabling users to explore their data visually.

## Features

- **Platform Selection**: Choose between YouTube, Instagram, and TikTok for data processing.
- **File Upload**: Upload multiple JSON files for each platform.
- **Data Processing**: Generates insights and visualizations from uploaded platform data.
- **Download CSV**: After processing, you can download a CSV file of the results.

## Setup

### Prerequisites

- Python 3.8+
- Flask and related dependencies

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/data-mirror-3.0.git
   cd data-mirror-3.0
   ```

2. **Set up a virtual environment** (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use .venv\Scripts\activate
   ```

3. **Install the dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables** (optional):

   - By default, the app runs in development mode. To switch to production, set the `FLASK_ENV` environment variable:

     ```bash
     export FLASK_ENV=production
     ```

5. **Run the application**:

   ```bash
   python app.py
   ```

6. **Access the app**:

   Open your browser and navigate to `http://127.0.0.1:5001`.

## Usage

1. **Landing Page**: 
   Start at the landing page and select your desired platform (YouTube, Instagram, TikTok) for data processing.

2. **Upload Data**: 
   Upload JSON files relevant to the platform. Only JSON files are supported for upload.

3. **View Insights**: 
   Once the data is processed, the dashboard will display insights and visualizations. You can also preview the first five rows of your data in a table.

4. **Download CSV**: 
   A downloadable CSV file will be generated for the processed data.

## File Structure

```
data-mirror-3.0/
│
├── app.py                     # Main Flask app
├── platforms/
│   ├── youtube.py              # YouTube processing logic
│   ├── instagram.py            # Instagram processing logic
│   └── tiktok.py               # Placeholder for TikTok processing logic
├── templates/
│   ├── homepage.html           # Landing page template
│   ├── platform_selection.html # Platform selection template
│   ├── dashboard_youtube.html  # YouTube dashboard template
│   ├── dashboard_instagram.html# Instagram dashboard template
│   ├── dashboard_tiktok.html   # TikTok dashboard template
├── static/                     # Static assets (CSS, JS, images)
└── README.md                   # This file
```

## Error Handling

- Errors encountered during file uploads or data processing are logged, and a relevant error message is displayed on the dashboard.
- The app gracefully handles shutdown requests using `SIGINT` and `SIGTERM`.

## Development

- The app uses `CORS` to handle cross-origin requests during development.
- Logging level is set to `DEBUG` in development mode to help troubleshoot issues.

### Running Tests

To be added.
