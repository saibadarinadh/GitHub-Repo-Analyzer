# GitHub Repository Analysis Tool

This application provides a comprehensive analysis of GitHub repositories. It fetches data using the GitHub API to offer insights into repository activity, contributors, issues, and more. The frontend is built with Flask and Bootstrap, providing a user-friendly interface to display the analysis results.

## Features

*   **Repository Overview**: Displays general information about the repository, such as description, stars, forks, and watchers.
*   **Contributor Analysis**: Lists top contributors, their number of contributions, and links to their GitHub profiles.
*   **Issue Tracking**: Summarizes open and closed issues, providing a snapshot of the project's health and development activity.
*   **Commit History**: Shows recent commit activity.
*   **Language Breakdown**: Visualizes the programming languages used in the repository.
*   **User-Friendly Interface**: Presents data in an easy-to-understand visual format using HTML templates and potentially charts.
*   **(Potentially AI-Powered Features from previous README)**: 
    *   AI-Powered Documentation Generation (READMEs, Usage Guides using Gemini AI)
    *   AI-Driven Code Quality Feedback

## Tech Stack

*   **Backend**: Python, Flask
*   **Frontend**: HTML, CSS, Bootstrap
*   **API**: GitHub REST API, Google Gemini API (for AI features)

## Project Structure (main_application)

```
main_application/
├── app.py                # Main Flask application file, handles routing and core logic
├── services/             # Contains business logic and external API interactions
│   └── analysis_service.py # Service layer for fetching and processing GitHub data
├── templates/            # HTML templates for rendering views
│   ├── index.html        # Main page for user input (repository URL)
│   ├── analysis.html     # Displays basic analysis results
│   └── Complete_analise.html # Displays a more detailed analysis
├── static/               # Static files (CSS, JavaScript, images)
│   └── css/
│       └── style.css     # Custom stylesheets (if any)
├── .env                  # Environment variables (e.g., GITHUB_TOKEN, GEMINI_API_KEY) - **DO NOT COMMIT THIS FILE**
├── .gitignore            # Specifies intentionally untracked files for Git
├── README.md             # This file: Project documentation
└── requirements.txt      # Python package dependencies (to be created)
```

## Setup and Installation

1.  **Clone the repository (if applicable):**
    If you're setting this up from a Git repository (replace with your actual URL if available):
    ```bash
    git clone https://github.com/yourusername/github-repo-analyzer.git
    cd main_application # Or cd github-repo-analyzer if that's the root
    ```

2.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    *   Create the environment (from within the `main_application` or project root directory):
        ```bash
        python -m venv venv
        ```
    *   Activate the environment:
        *   Windows (PowerShell/CMD):
            ```bash
            .\venv\Scripts\activate
            ```
        *   macOS/Linux (bash/zsh):
            ```bash
            source venv/bin/activate
            ```

3.  **Install Dependencies:**
    A `requirements.txt` file lists all the Python packages needed for the project.
    ```bash
    pip install -r requirements.txt
    ```
    *(If `requirements.txt` doesn't exist yet, I can help you create one. Common libraries for this project would be Flask, requests, python-dotenv, and google-generativeai.)*

4.  **Set up Environment Variables:**
    Create a `.env` file in the `main_application` (or project root) directory. This file will store sensitive information like API keys. Add your GitHub Personal Access Token and Gemini API Key to this file:
    ```env
    GITHUB_TOKEN=your_github_personal_access_token_here
    GEMINI_API_KEY=your_gemini_api_key_here
    ```
    **Important**: Ensure `.env` is listed in your `.gitignore` file to prevent committing sensitive keys to version control.

## Running the Application

1.  Ensure your virtual environment is activated and dependencies are installed.
2.  Make sure the `.env` file is correctly set up with your API keys.
3.  Run the Flask application from the `main_application` (or project root) directory where `app.py` is located:
    ```bash
    python app.py
    ```
    Alternatively, if you prefer using the Flask CLI (ensure `FLASK_APP` environment variable is set to `app.py` if running from outside the directory containing `app.py`):
    ```bash
    flask run
    ```
4.  Open your web browser and navigate to `http://127.0.0.1:5000/` (or the port specified in your application's output).

## Usage

1.  Once the application is running, open the provided URL in your browser.
2.  On the main page (`index.html`), you will find an input field to enter the URL of the GitHub repository you wish to analyze (e.g., `https://github.com/owner/repository-name`).
3.  Select one of the available analysis options (e.g., Generate README, Code Quality & Feedback, How to Use Repository Guide).
4.  Click the "Analyze" button.
5.  The application will fetch data from the GitHub API (and potentially Gemini API) and display the analysis results.
6.  You can choose to view results in a Normal or Developer view as per the application's design.

## Troubleshooting

*   **`KeyError` or `TypeError` related to GitHub API data**:
    *   Ensure your `GITHUB_TOKEN` is valid, has the necessary permissions, and is correctly set in your `.env` file.
    *   The GitHub API response structure might have changed or might differ for certain repositories. Debug by printing the API response in `services/analysis_service.py` to inspect the actual data structure.
    *   The MEMORY `98ff956b-b0e4-4859-9bda-0865373e83a8` indicates a past issue with list indices vs. string keys (e.g., `contributor['login']` vs `contributor.username`). Double-check data access in your templates and Python code when dealing with API responses.
*   **Gemini API Issues**: 
    *   Ensure your `GEMINI_API_KEY` is valid and correctly set in your `.env` file.
    *   Check for any specific error messages returned by the Gemini API.
*   **Rate Limiting**: If you make too many requests to the GitHub API or Gemini API without a token or exceed the authenticated rate limit, you might encounter errors. Using tokens helps increase these limits.
*   **Template Not Found**: Ensure your Flask routes correctly render the specified HTML templates and that the template files exist in the `templates` directory with the correct names.
*   **ModuleNotFoundError**: If you get errors about missing modules, ensure you have activated your virtual environment and installed all dependencies from `requirements.txt`.

## Contributing

If you'd like to contribute to this project:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/AmazingFeature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
5.  Push to the branch (`git push origin feature/AmazingFeature`).
6.  Open a Pull Request.

Please ensure your code adheres to any existing style guidelines and that all tests pass.
