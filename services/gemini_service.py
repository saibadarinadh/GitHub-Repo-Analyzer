import requests
import os
from typing import Dict, Any, Optional, List
import json
import re

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"

    def generate_content(self, prompt: str) -> str:
        """Generate content using Gemini API."""
        if not self.api_key:
            return "Error: Gemini API key not configured. Please set GEMINI_API_KEY environment variable."

        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    print(f"Unexpected API response: {result}")
                    return self._generate_fallback_response(prompt)
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return self._generate_fallback_response(prompt)
        except Exception as e:
            print(f"Exception in generate_content: {str(e)}")
            return self._generate_fallback_response(prompt)

    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate a fallback response when the API fails."""
        if "README.md" in prompt:
            repo_name = prompt.split("'")[1] if "'" in prompt else "the repository"
            return f"""# {repo_name}

## Description
A comprehensive project for {repo_name}.

## Features
- Modern architecture
- Well-structured codebase
- Comprehensive documentation

## Installation
```bash
git clone https://github.com/username/{repo_name}.git
cd {repo_name}
```

## Usage
Please refer to the documentation for detailed usage instructions.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the terms of the license included in the repository."""
        return "Error: Unable to generate content. Please try again later."

    def generate_readme(self, repo_data: Dict[str, Any], existing_readme: Optional[str], 
                       code_analysis: Dict[str, Any], stats: Dict[str, Any]) -> str:
        """Generate a comprehensive README file."""
        # Create a detailed prompt for README generation
        prompt = f"""You are a technical documentation expert. Generate a comprehensive README.md file for the GitHub repository '{repo_data['name']}'.
        
Repository Information:
- Description: {repo_data.get('description', 'No description provided')}
- Stars: {repo_data.get('stargazers_count', 0)}
- Forks: {repo_data.get('forks_count', 0)}
- Language: {repo_data.get('language', 'Unknown')}
- Clone URL: {repo_data.get('clone_url', '')}
- Homepage: {repo_data.get('homepage', '')}

Code Analysis:
- Total Files: {code_analysis['total_files']}
- Languages Used: {json.dumps(code_analysis['languages'])}
- Main Files: {json.dumps(code_analysis['main_files'])}
- Dependencies: {json.dumps(list(code_analysis['dependencies']))}
- Architecture Patterns: {json.dumps(code_analysis['architecture'])}

Repository Statistics:
- Contributors: {len(stats['contributors'])}
- Open Issues: {len(stats['issues'])}
- Commit Activity: {json.dumps(stats['commit_activity'])}

Existing README Content (if any):
{existing_readme if existing_readme else 'No existing README found'}

Based on the above information, generate a professional README.md that includes:

1. Project Title and Description
   - Clear project name with emoji
   - Brief description of what the project does
   - Key features and capabilities
   - Add badges for stars, forks, and language

2. Installation Instructions
   - Prerequisites
   - Step-by-step installation guide
   - Environment setup
   - Dependencies installation

3. Usage Guide
   - Basic usage examples
   - Code snippets
   - Configuration options
   - Screenshots if available

4. Project Structure
   - Main components
   - Key files and their purposes
   - Architecture overview
   - Directory structure

5. Dependencies and Requirements
   - List of required packages with versions
   - Environment requirements
   - System requirements

6. Contributing Guidelines
   - How to contribute
   - Code style guide
   - Pull request process
   - Development setup

7. License Information
   - License type
   - Copyright notice
   - License file link

8. Contact Information
   - Author/maintainer details
   - Support channels
   - Issue reporting

Format the README with:
- Clear section headers using Markdown
- Code blocks with syntax highlighting
- Tables for structured information
- Lists for better readability
- Emojis for visual appeal
- Badges for build status, version, etc.
- Screenshots or diagrams if mentioned in the description

Make sure the README is:
- Professional and well-structured
- Easy to understand
- Comprehensive yet concise
- Follows GitHub's best practices
- Includes all necessary information for users and contributors

IMPORTANT FORMATTING RULES:
1. Each section should be separated by a blank line
2. Use proper markdown headers (# for main title, ## for sections, ### for subsections)
3. Lists should be properly indented
4. Code blocks should be properly fenced with ```
5. Tables should be properly aligned
6. Badges should be on the same line as the title
7. Each feature or point should be on a new line
8. Use proper spacing between sections
9. Ensure all links are properly formatted
10. Use consistent emoji placement

Example format:
```markdown
# Project Name 🚀

[![Stars](https://img.shields.io/github/stars/username/repo?style=social)](https://github.com/username/repo/stargazers)
[![Forks](https://img.shields.io/github/forks/username/repo?style=social)](https://github.com/username/repo/network/members)
[![Language](https://img.shields.io/github/languages/top/username/repo)](https://github.com/username/repo)

## Description
Brief description of the project.

## Features
- Feature 1
- Feature 2
- Feature 3

## Installation
```bash
git clone https://github.com/username/repo.git
cd repo
```

## Usage
```python
# Example code
print("Hello, World!")
```

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
- Author: Your Name
- Email: your.email@example.com
```"""

        content = self.generate_content(prompt)
        if content.startswith("Error:"):
            # Fallback to a simpler README if the API fails
            return self._generate_fallback_readme(repo_data, code_analysis)
        return content

    def _generate_fallback_readme(self, repo_data: Dict[str, Any], code_analysis: Dict[str, Any]) -> str:
        """Generate a basic README when the API fails."""
        return f"""# {repo_data['name']} 🚀

[![Stars](https://img.shields.io/github/stars/{repo_data['full_name']}?style=social)](https://github.com/{repo_data['full_name']}/stargazers)
[![Forks](https://img.shields.io/github/forks/{repo_data['full_name']}?style=social)](https://github.com/{repo_data['full_name']}/network/members)
[![Language](https://img.shields.io/github/languages/top/{repo_data['full_name']})](https://github.com/{repo_data['full_name']})

## Description
{repo_data.get('description', 'No description provided')}

## Features
- Built with {', '.join(code_analysis['languages'].keys())}
- {len(code_analysis['main_files'])} main components
- {len(code_analysis['dependencies'])} dependencies

## Installation
```bash
git clone {repo_data.get('clone_url', f'https://github.com/username/{repo_data["name"]}.git')}
cd {repo_data['name']}
```

## Dependencies
{', '.join(code_analysis['dependencies'])}

## Usage
Please refer to the code examples in the repository.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the terms of the license included in the repository.

## Contact
For support, please open an issue in the repository."""

    def analyze_readme(self, readme_content: str) -> str:
        """Analyze README content and provide insights."""
        prompt = f"""Analyze the following README content and provide insights on:
1. Project Purpose and Goals
2. Key Features and Capabilities
3. Technical Requirements
4. Documentation Quality
5. Project Maturity

README Content:
{readme_content}

Please provide a detailed analysis focusing on these aspects."""

        return self.generate_content(prompt)

    def analyze_issues(self, issues: List[Dict[str, Any]]) -> str:
        """Analyze repository issues and provide insights."""
        issues_text = "\n".join([
            f"- {issue['title']} ({issue['state']})"
            for issue in issues
        ])
        
        prompt = f"""Analyze the following GitHub issues and provide insights on:
1. Common Themes and Patterns
2. Priority Areas for Improvement
3. Project Health Indicators
4. Suggested Action Items

Issues:
{issues_text}

Please provide a detailed analysis focusing on these aspects."""

        return self.generate_content(prompt)

    def _assess_complexity(self, code_analysis: Dict[str, Any]) -> str:
        """Assess the complexity level of the repository."""
        total_files = code_analysis.get('total_files', 0)
        languages = len(code_analysis.get('languages', {}))
        dependencies = len(code_analysis.get('dependencies', []))
        architecture = len(code_analysis.get('architecture', []))
        
        complexity_score = (total_files * 0.3) + (languages * 0.2) + (dependencies * 0.3) + (architecture * 0.2)
        
        if complexity_score > 50:
            return 'high'
        elif complexity_score > 20:
            return 'medium'
        else:
            return 'low'

    def _extract_tech_stack(self, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and categorize the technology stack."""
        languages = code_analysis.get('languages', {})
        dependencies = code_analysis.get('dependencies', [])
        architecture = code_analysis.get('architecture', [])
        
        return {
            'languages': languages,
            'frameworks': [dep for dep in dependencies if any(fw in dep.lower() for fw in ['framework', 'django', 'flask', 'react', 'vue', 'angular'])],
            'libraries': [dep for dep in dependencies if not any(fw in dep.lower() for fw in ['framework', 'django', 'flask', 'react', 'vue', 'angular'])],
            'architecture': architecture
        }

    def _create_comprehensive_prompt(self, repo_data: Dict[str, Any], existing_readme: Optional[str],
                                   code_analysis: Dict[str, Any], stats: Dict[str, Any],
                                   repo_type: str, complexity_level: str, tech_stack: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for README generation."""
        
        # Base template for different repository types
        templates = {
            'machine_learning': self._get_ml_template(),
            'web_application': self._get_web_template(),
            'data_science': self._get_ds_template(),
            'ai_ml_project': self._get_ai_ml_template(),
            'general_software': self._get_general_template()
        }
        
        template = templates.get(repo_type, templates['general_software'])
        
        # Format the prompt with repository data
        prompt = f"""You are a technical documentation expert. Generate a comprehensive README.md file for the GitHub repository '{repo_data['name']}'.
        
Repository Information:
- Description: {repo_data.get('description', 'No description provided')}
- Stars: {repo_data.get('stargazers_count', 0)}
- Forks: {repo_data.get('forks_count', 0)}
- Language: {repo_data.get('language', 'Unknown')}
- Clone URL: {repo_data.get('clone_url', '')}
- Homepage: {repo_data.get('homepage', '')}

Code Analysis:
- Total Files: {code_analysis['total_files']}
- Languages Used: {json.dumps(code_analysis['languages'])}
- Main Files: {json.dumps(code_analysis['main_files'])}
- Dependencies: {json.dumps(list(code_analysis['dependencies']))}
- Architecture Patterns: {json.dumps(code_analysis['architecture'])}

Repository Statistics:
- Contributors: {len(stats['contributors'])}
- Open Issues: {len(stats['issues'])}
- Commit Activity: {json.dumps(stats['commit_activity'])}

Project Characteristics:
- Type: {repo_type}
- Complexity: {complexity_level}
- Tech Stack: {json.dumps(tech_stack)}

Existing README Content (if any):
{existing_readme if existing_readme else 'No existing README found'}

{template}

IMPORTANT FORMATTING RULES:
1. Each section must be separated by TWO blank lines
2. Each subsection must be separated by ONE blank line
3. Lists must be properly indented with TWO spaces
4. Code blocks must be properly fenced with ```
5. Tables must be properly aligned with |
6. Each feature or point must be on a new line
7. Use consistent emoji placement
8. Use proper markdown headers (# for main title, ## for sections, ### for subsections)
9. Ensure all links are properly formatted
10. Use proper spacing in lists and tables"""

        return prompt

    def _get_ml_template(self) -> str:
        """Get template for machine learning projects."""
        return """Generate a README that includes:

1. Project Title and Description
   - Clear project name with relevant emoji
   - Brief description of the ML model/problem
   - Key features and capabilities

2. Model Architecture
   - Detailed model structure
   - Input/output specifications
   - Training methodology

3. Dataset Information
   - Dataset source and description
   - Data preprocessing steps
   - Data augmentation techniques

4. Performance Metrics
   - Model accuracy and other metrics
   - Comparison with baseline
   - Performance visualization

5. Installation and Setup
   - Environment requirements
   - Dependencies installation
   - Configuration steps

6. Usage Guide
   - Model training instructions
   - Inference examples
   - API documentation

7. Results and Examples
   - Sample predictions
   - Visualization examples
   - Use cases

8. Contributing Guidelines
   - Development setup
   - Code style guide
   - Pull request process"""

    def _get_web_template(self) -> str:
        """Get template for web applications."""
        return """Generate a README that includes:

1. Project Title and Description
   - Clear project name with relevant emoji
   - Brief description of the web application
   - Key features and capabilities

2. Tech Stack
   - Frontend technologies
   - Backend technologies
   - Database and storage
   - Deployment platform

3. Features
   - User interface features
   - Backend functionality
   - API endpoints
   - Authentication system

4. Installation
   - Prerequisites
   - Environment setup
   - Configuration
   - Database setup

5. Usage Guide
   - Running the application
   - API documentation
   - Environment variables
   - Deployment instructions

6. Project Structure
   - Directory organization
   - Key components
   - Architecture diagram

7. Contributing
   - Development setup
   - Code style guide
   - Testing guidelines"""

    def _get_ds_template(self) -> str:
        """Get template for data science projects."""
        return """Generate a README that includes:

1. Project Title and Description
   - Clear project name with relevant emoji
   - Brief description of the data analysis
   - Key findings and insights

2. Data Analysis
   - Dataset description
   - Analysis methodology
   - Key metrics and findings
   - Visualizations

3. Technical Details
   - Analysis tools used
   - Data processing pipeline
   - Statistical methods
   - Visualization techniques

4. Results
   - Key findings
   - Statistical significance
   - Visual representations
   - Conclusions

5. Usage Guide
   - Environment setup
   - Running the analysis
   - Reproducing results
   - Customizing analysis

6. Contributing
   - Development setup
   - Code style guide
   - Analysis guidelines"""

    def _get_ai_ml_template(self) -> str:
        """Get template for AI/ML projects."""
        return """Generate a README that includes:

1. Project Title and Description
   - Clear project name with relevant emoji
   - Brief description of the AI/ML solution
   - Key features and capabilities

2. Model Architecture
   - Neural network structure
   - Training methodology
   - Hyperparameters
   - Model variants

3. Technical Implementation
   - Framework details
   - Training pipeline
   - Inference process
   - Performance optimization

4. Results
   - Model performance
   - Benchmark comparisons
   - Use case examples
   - Limitations

5. Usage Guide
   - Environment setup
   - Model training
   - Inference examples
   - API documentation

6. Contributing
   - Development setup
   - Code style guide
   - Model improvement guidelines"""

    def _get_general_template(self) -> str:
        """Get template for general software projects."""
        return """Generate a README that includes:

1. Project Title and Description
   - Clear project name with relevant emoji
   - Brief description of the project
   - Key features and capabilities

2. Features
   - Main functionality
   - Key components
   - Technical capabilities
   - Use cases

3. Installation
   - Prerequisites
   - Setup instructions
   - Configuration
   - Dependencies

4. Usage Guide
   - Basic usage
   - Advanced features
   - Examples
   - API documentation

5. Contributing
   - Development setup
   - Code style guide
   - Pull request process"""

    def _post_process_readme(self, content: str, repo_data: Dict[str, Any]) -> str:
        """Post-process the generated README content."""
        # Add repository badges
        badges = f"""[![Stars](https://img.shields.io/github/stars/{repo_data['full_name']}?style=social)](https://github.com/{repo_data['full_name']}/stargazers)
[![Forks](https://img.shields.io/github/forks/{repo_data['full_name']}?style=social)](https://github.com/{repo_data['full_name']}/network/members)
[![Language](https://img.shields.io/github/languages/top/{repo_data['full_name']})](https://github.com/{repo_data['full_name']})"""

        # Insert badges after the title
        content = re.sub(r'^# (.*?)\n', f'# \\1\n\n{badges}\n', content)
        
        # Ensure proper spacing
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()

    def _generate_enhanced_fallback_readme(self, repo_data: Dict[str, Any], 
                                         code_analysis: Dict[str, Any], 
                                         repo_type: str) -> str:
        """Generate an enhanced fallback README when the API fails."""
        return f"""# {repo_data['name']}

[![Stars](https://img.shields.io/github/stars/{repo_data['full_name']}?style=social)](https://github.com/{repo_data['full_name']}/stargazers)
[![Forks](https://img.shields.io/github/forks/{repo_data['full_name']}?style=social)](https://github.com/{repo_data['full_name']}/network/members)
[![Language](https://img.shields.io/github/languages/top/{repo_data['full_name']})](https://github.com/{repo_data['full_name']})

## 🔬 Project Overview
{repo_data.get('description', 'No description provided')}

## 🚀 Key Features
- Built with {', '.join(code_analysis['languages'].keys())}
- {len(code_analysis['main_files'])} main components
- {len(code_analysis['dependencies'])} dependencies

## 📦 Installation

### Prerequisites
- Python 3.x
- Git

### Step 1: Clone Repository
```bash
git clone {repo_data.get('clone_url', f'https://github.com/username/{repo_data["name"]}.git')}
cd {repo_data['name']}
```

## 📚 Dependencies
{', '.join(code_analysis['dependencies'])}

## 🤝 Contributing
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Submit pull request

## 📜 License
This project is licensed under the terms of the license included in the repository.

## 📧 Contact
For support, please open an issue in the repository.""" 