import requests
import os
import base64
from typing import Dict, Any, List, Optional, Tuple
import json
import time
from datetime import datetime, timedelta
import logging
from ratelimit import limits, sleep_and_retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.rate_limit_remaining = 5000  # Default value
        self.rate_limit_reset = 0
        self.use_api = True  # Flag to control API usage
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum time between requests (100ms)

    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limit information from response headers."""
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        if 'X-RateLimit-Reset' in response.headers:
            self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])

    def _should_use_api(self) -> bool:
        """Determine whether to use API or fallback to git."""
        if not self.use_api:
            return False
        if self.rate_limit_remaining <= 10:  # Switch to git if few requests remaining
            self.use_api = False
            logger.warning("Switching to git fallback due to low rate limit")
            return False
        return True

    def _wait_for_rate_limit(self) -> None:
        """Wait if rate limit is close to being exceeded."""
        current_time = time.time()
        if current_time < self.rate_limit_reset and self.rate_limit_remaining <= 10:
            wait_time = self.rate_limit_reset - current_time + 1
            logger.info(f"Rate limit nearly exceeded. Waiting for {wait_time} seconds")
            time.sleep(wait_time)

    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Tuple[Optional[requests.Response], bool]:
        """Make an API request with rate limit handling."""
        if not self._should_use_api():
            return None, False

        # Ensure minimum time between requests
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)

        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            self.last_request_time = time.time()
            self._handle_rate_limit(response)

            if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
                logger.warning("Rate limit exceeded, switching to git fallback")
                self.use_api = False
                return None, False

            return response, True
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None, False

    def get_repository(self, username: str, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information with fallback."""
        url = f"{self.base_url}/repos/{username}/{repo_name}"
        response, used_api = self._make_request(url)
        
        if used_api and response and response.status_code == 200:
            return response.json()
        
        # Fallback to git command
        try:
            # Implement git fallback logic here
            logger.info("Using git fallback for repository info")
            return self._get_repo_info_git(username, repo_name)
        except Exception as e:
            logger.error(f"Git fallback failed: {str(e)}")
            return None

    def get_readme(self, username: str, repo_name: str) -> Optional[str]:
        """Get repository README content."""
        # Try different README filenames
        readme_files = ['README.md', 'README', 'readme.md', 'Readme.md']
        
        for readme_file in readme_files:
            url = f"{self.base_url}/repos/{username}/{repo_name}/contents/{readme_file}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                content = response.json()
                if 'content' in content:
                    try:
                        # Decode base64 content
                        decoded_content = base64.b64decode(content['content']).decode('utf-8')
                        return decoded_content
                    except Exception as e:
                        print(f"Error decoding README content: {str(e)}")
                        continue
        
        return None

    def get_repository_contents(self, username: str, repo_name: str, path: str = "") -> List[Dict[str, Any]]:
        """Get repository contents recursively."""
        url = f"{self.base_url}/repos/{username}/{repo_name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return []
            
        contents = response.json()
        if not isinstance(contents, list):
            return []
            
        all_contents = []
        for item in contents:
            if item['type'] == 'file':
                all_contents.append(item)
            elif item['type'] == 'dir':
                # Recursively get contents of subdirectories
                sub_contents = self.get_repository_contents(username, repo_name, item['path'])
                all_contents.extend(sub_contents)
                
        return all_contents

    def get_file_content(self, username: str, repo_name: str, path: str) -> Optional[str]:
        """Get content of a specific file."""
        url = f"{self.base_url}/repos/{username}/{repo_name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            content = response.json()
            if 'content' in content:
                try:
                    # Decode base64 content
                    decoded_content = base64.b64decode(content['content'])
                    
                    # Check if it's a binary file
                    if self._is_binary_file(path):
                        return None
                        
                    # Try different encodings
                    encodings = ['utf-8', 'latin-1', 'cp1252']
                    for encoding in encodings:
                        try:
                            return decoded_content.decode(encoding)
                        except UnicodeDecodeError:
                            continue
                            
                    # If all encodings fail, return None
                    return None
                except Exception as e:
                    print(f"Error decoding file content: {str(e)}")
                    return None
        return None

    def _is_binary_file(self, filename: str) -> bool:
        """Check if a file is likely to be binary."""
        binary_extensions = {
            # Images
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz',
            # Executables
            '.exe', '.dll', '.so', '.dylib',
            # Other binary formats
            '.bin', '.dat', '.db', '.sqlite'
        }
        return any(filename.lower().endswith(ext) for ext in binary_extensions)

    def get_contributors(self, username: str, repo_name: str) -> List[Dict[str, Any]]:
        """Get repository contributors."""
        url = f"{self.base_url}/repos/{username}/{repo_name}/contributors"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return []

    def get_commit_activity(self, username: str, repo_name: str) -> List[Dict[str, Any]]:
        """Get enhanced commit activity with frequency metrics."""
        url = f"{self.base_url}/repos/{username}/{repo_name}/stats/commit_activity"
        response, used_api = self._make_request(url)
        
        if used_api and response and response.status_code == 200:
            activity_data = response.json()
            return self._enhance_commit_metrics(activity_data)
        
        # Fallback to git command
        try:
            logger.info("Using git fallback for commit activity")
            return self._get_commit_activity_git(username, repo_name)
        except Exception as e:
            logger.error(f"Git fallback failed: {str(e)}")
            return []

    def _enhance_commit_metrics(self, activity_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance commit activity data with additional metrics."""
        enhanced_data = []
        total_commits = sum(week['total'] for week in activity_data)
        
        for week in activity_data:
            enhanced_week = week.copy()
            enhanced_week['commit_frequency'] = week['total'] / 7 if week['total'] > 0 else 0
            enhanced_week['percentage_of_total'] = (week['total'] / total_commits * 100) if total_commits > 0 else 0
            enhanced_data.append(enhanced_week)
        
        return enhanced_data

    def _get_repo_info_git(self, username: str, repo_name: str) -> Optional[Dict[str, Any]]:
        """Fallback method to get repository info using git commands."""
        try:
            import subprocess
            from pathlib import Path
            import tempfile

            # Create temporary directory for git clone
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_url = f"https://github.com/{username}/{repo_name}.git"
                
                # Clone repository
                subprocess.run(['git', 'clone', '--depth', '1', repo_url, temp_dir], 
                             check=True, capture_output=True)
                
                # Get repository info
                repo_path = Path(temp_dir)
                
                # Get commit count
                commit_count = subprocess.run(
                    ['git', 'rev-list', '--count', 'HEAD'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True
                ).stdout.strip()
                
                # Get last commit date
                last_commit = subprocess.run(
                    ['git', 'log', '-1', '--format=%cd'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True
                ).stdout.strip()
                
                # Get branch count
                branch_count = subprocess.run(
                    ['git', 'branch', '-r'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True
                ).stdout.count('\n')
                
                return {
                    'name': repo_name,
                    'full_name': f"{username}/{repo_name}",
                    'description': self._get_repo_description_git(temp_dir),
                    'stargazers_count': 0,  # Not available via git
                    'forks_count': 0,  # Not available via git
                    'open_issues_count': 0,  # Not available via git
                    'commit_count': int(commit_count),
                    'last_commit_date': last_commit,
                    'branch_count': branch_count,
                    'source': 'git_fallback'
                }
        except Exception as e:
            logger.error(f"Git fallback failed: {str(e)}")
            return None

    def _get_repo_description_git(self, repo_path: str) -> str:
        """Get repository description from git config."""
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.description'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or "No description available"
        except Exception:
            return "No description available"

    def _get_commit_activity_git(self, username: str, repo_name: str) -> List[Dict[str, Any]]:
        """Fallback method to get commit activity using git commands."""
        try:
            import subprocess
            from datetime import datetime, timedelta
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                repo_url = f"https://github.com/{username}/{repo_name}.git"
                
                # Clone repository
                subprocess.run(['git', 'clone', '--depth', '1', repo_url, temp_dir], 
                             check=True, capture_output=True)
                
                # Get commit activity for the last year
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                # Get commit activity by week
                activity_data = []
                current_date = start_date
                
                while current_date < end_date:
                    week_end = current_date + timedelta(days=7)
                    
                    # Get commits for the week
                    commits = subprocess.run(
                        ['git', 'log', '--since', current_date.isoformat(),
                         '--until', week_end.isoformat(), '--format=%H'],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True
                    ).stdout.strip().split('\n')
                    
                    # Count commits
                    commit_count = len([c for c in commits if c])
                    
                    activity_data.append({
                        'week': int(current_date.timestamp()),
                        'total': commit_count,
                        'days': [0] * 7,  # Not available via git
                        'commit_frequency': commit_count / 7 if commit_count > 0 else 0,
                        'source': 'git_fallback'
                    })
                    
                    current_date = week_end
                
                return activity_data
        except Exception as e:
            logger.error(f"Git commit activity fallback failed: {str(e)}")
            return []

    def _get_commit_frequency_metrics(self, activity_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate commit frequency metrics."""
        if not activity_data:
            return {
                'daily_average': 0,
                'weekly_average': 0,
                'monthly_average': 0,
                'busiest_day': None,
                'busiest_week': None
            }
        
        total_commits = sum(week['total'] for week in activity_data)
        total_weeks = len(activity_data)
        
        # Calculate averages
        daily_average = total_commits / (total_weeks * 7) if total_weeks > 0 else 0
        weekly_average = total_commits / total_weeks if total_weeks > 0 else 0
        monthly_average = (total_commits / total_weeks) * 4 if total_weeks > 0 else 0
        
        # Find busiest periods
        busiest_week = max(activity_data, key=lambda x: x['total'])
        busiest_day = max(busiest_week['days']) if 'days' in busiest_week else 0
        
        return {
            'daily_average': round(daily_average, 2),
            'weekly_average': round(weekly_average, 2),
            'monthly_average': round(monthly_average, 2),
            'busiest_day': busiest_day,
            'busiest_week': busiest_week['week'] if busiest_week else None,
            'total_commits': total_commits,
            'total_weeks': total_weeks
        }

    def get_issues(self, username: str, repo_name: str) -> List[Dict[str, Any]]:
        """Get repository issues."""
        url = f"{self.base_url}/repos/{username}/{repo_name}/issues"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return []

    def get_languages(self, username: str, repo_name: str) -> Dict[str, int]:
        """Get repository languages."""
        url = f"{self.base_url}/repos/{username}/{repo_name}/languages"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return {} 