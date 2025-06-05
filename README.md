# GitHub Repository Analyzer

A powerful tool that analyzes GitHub repositories using AI to provide insights, generate documentation, and offer code quality feedback.

## Features

- **Repository Analysis**: Get comprehensive insights about any GitHub repository
- **AI-Powered Documentation**: Generate README files and usage guides using Google's Gemini AI
- **Code Quality Feedback**: Receive detailed feedback about code quality and improvement areas
- **Developer View**: Special view for developers with technical metrics and guidelines
- **Multiple Analysis Options**:
  - Generate README
  - Code Quality & Feedback
  - How to Use Repository Guide

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/github-repo-analyzer.git
cd github-repo-analyzer
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_token
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

1. Enter a GitHub repository URL in the format: `https://github.com/username/repository`
2. Choose one of the three analysis options:
   - Generate README: Creates a comprehensive README file
   - Code Quality & Feedback: Provides code quality analysis and improvement suggestions
   - How to Use Repo: Generates a detailed usage guide

3. View the results in either Normal or Developer view

## API Keys

- **Gemini API**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **GitHub Token**: Create a personal access token from [GitHub Settings](https://github.com/settings/tokens)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 