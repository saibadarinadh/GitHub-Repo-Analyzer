from typing import Optional, Tuple

def validate_repo_url(repo_url: str) -> Optional[Tuple[str, str]]:
    """Validate GitHub repository URL and extract username and repo name."""
    try:
        # Clean up the URL
        repo_url = repo_url.strip().replace('https://github.com/', '').replace('http://github.com/', '')
        parts = repo_url.strip('/').split('/')
        if len(parts) >= 2:
            username = parts[0]
            repo_name = parts[1]
            return username, repo_name
        return None
    except Exception as e:
        print(f"Error parsing URL: {str(e)}")
        return None 