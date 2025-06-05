import requests
from datetime import datetime

def handle_api_error(response: requests.Response) -> str:
    """Handle API errors and return appropriate error message."""
    if response.status_code == 404:
        return "Repository not found. Please check the URL and try again."
    elif response.status_code == 403:
        rate_limit = response.headers.get('X-RateLimit-Remaining')
        if rate_limit == '0':
            reset_time = response.headers.get('X-RateLimit-Reset')
            if reset_time:
                reset = datetime.fromtimestamp(int(reset_time))
                return f"Rate limit exceeded. Please try again after {reset.strftime('%H:%M:%S')}"
            return "Rate limit exceeded. Please try again later."
    try:
        error_data = response.json()
        return error_data.get('message', 'An error occurred while fetching data.')
    except:
        return f"API Error {response.status_code}: {response.text}" 