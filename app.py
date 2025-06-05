from flask import Flask, render_template, request, jsonify, redirect
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from dotenv import load_dotenv
import os
from services.github_service import GitHubService
from services.gemini_service import GeminiService
from services.analysis_service import AnalysisService
from utils.error_handler import handle_api_error
from utils.url_validator import validate_repo_url

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize services
github_service = GitHubService()
gemini_service = GeminiService()
analysis_service = AnalysisService()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        repo_url = request.form.get('repo_url')
        view_type = request.form.get('viewType', 'normal')
        action = request.form.get('action')
        
        if repo_url:
            try:
                # Validate and parse repository URL
                repo_info = validate_repo_url(repo_url)
                if not repo_info:
                    error = "Invalid GitHub repository URL. Please enter a valid URL like 'https://github.com/username/repo'."
                    return render_template('index.html', error=error)
                
                username, repo_name = repo_info
                
                # Get repository data
                repo_data = github_service.get_repository(username, repo_name)
                if not repo_data:
                    error = "Failed to fetch repository data"
                    return render_template('index.html', error=error)
                
                # Get analysis based on action
                if action == 'generate_readme':
                    result = analysis_service.generate_readme(username, repo_name)
                    if 'error' in result:
                        return render_template('index.html', error=result['error'])
                    return render_template('analysis.html', 
                                        username=username,
                                        repo_name=repo_name,
                                        analysis_type='readme',
                                        readme_content=result['readme_content'],
                                        analysis=result['analysis'])
                elif action == 'code_feedback':
                    try:
                        result = analysis_service.get_code_feedback(username, repo_name)
                        if not result or 'error' in result:
                            error = result.get('error', "Failed to generate code feedback")
                            return render_template('index.html', error=error)
                        
                        return render_template('analysis.html',
                                            username=username,
                                            repo_name=repo_name,
                                            analysis_type='code_feedback',
                                            code_feedback=result)
                    except Exception as e:
                        error = f"Error generating code feedback: {str(e)}"
                        print(f"Full error: {e}")
                        return render_template('index.html', error=error)
                elif action == 'complete_analysis':
                    try:
                        view_type = request.form.get('view_type', 'repo') # Default to 'repo'

                        if view_type == 'repo':
                            result = analysis_service.get_full_analysis(username, repo_name)

                            # CRITICAL CHECK: Ensure result is a dictionary
                            if not isinstance(result, dict):
                                print(f"CRITICAL ERROR: analysis_service.get_full_analysis did not return a dict. Got: {type(result)}")
                                return render_template('index.html', error="Internal server error: Invalid analysis data format.")

                            if result.get('error'): # Now this is safe
                                error = result.get('error', "Failed to generate complete analysis")
                                return render_template('index.html', error=error)
                            
                            # DEBUG: Print structure of result for troubleshooting
                            print('DEBUG: result type:', type(result))
                            if isinstance(result, dict):
                                for k, v in result.items():
                                    print(f'DEBUG: result["{k}"] type:', type(v))
                                    if isinstance(v, dict):
                                        for sk, sv in v.items():
                                            print(f'    DEBUG: result["{k}"]["{sk}"] type:', type(sv))
                                    elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                                        print(f'    DEBUG: result["{k}"][0] keys:', v[0].keys())

                            # Safely access nested dictionaries
                            metrics_accessor_dict = result.get('metrics', {})
                            if not isinstance(metrics_accessor_dict, dict):
                                metrics_accessor_dict = {}

                            issues_accessor_dict = result.get('issues', {})
                            if not isinstance(issues_accessor_dict, dict):
                                issues_accessor_dict = {}
                            
                            code_analysis_accessor_dict = result.get('code_analysis', {})
                            if not isinstance(code_analysis_accessor_dict, dict):
                                code_analysis_accessor_dict = {}

                            # Process contributors data (Corrected and Robust)
                            contributors = [] # Initialize
                            raw_contributors_list = result.get('contributors', []) # Safely get the list
                            if isinstance(raw_contributors_list, list):
                                processed_list = []
                                for item in raw_contributors_list: # Iterate over the safely fetched list
                                    if isinstance(item, dict):
                                        processed_list.append({
                                            'username': item.get('login', 'N/A_login_missing'), # Safely get login
                                            'contributions': item.get('contributions', 0) # Safely get contributions
                                        })
                                    else:
                                        # Handle cases where an item in the contributors list isn't a dictionary
                                        processed_list.append({
                                            'username': 'N/A_item_not_dict',
                                            'contributions': 0
                                        })
                                contributors = processed_list

                            # Process issues data
                            raw_issues_list = issues_accessor_dict.get('issues', [])
                            issues = [] # This will store the processed list of issue dicts
                            if isinstance(raw_issues_list, list):
                                issues = [
                                    {
                                        'title': i.get('title', ''),
                                        'state': i.get('state', ''),
                                        'created_at': i.get('created_at', '')
                                    }
                                    for i in raw_issues_list if isinstance(i, dict)
                                ]

                            # Process code analysis data (using accessor dict)
                            languages = code_analysis_accessor_dict.get('languages', {})
                            if not isinstance(languages, dict):
                                languages = {}

                            # Process commit activity data
                            commit_activity = result.get('commit_activity', []) # Assumed to be a list directly under result
                            if not isinstance(commit_activity, list):
                                commit_activity = []
                            
                            weeks = result.get('weeks', []) # Assumed to be a list directly under result
                            if not isinstance(weeks, list):
                                weeks = []

                            # Create the final analysis result
                            analysis_result = {
                                'name': result.get('name', ''),
                                'stars': result.get('stars', 0),
                                'forks': result.get('forks', 0),
                                'watchers': result.get('watchers', 0),
                                'description': result.get('description', 'No description provided'),
                                'language': result.get('language', 'Unknown'),
                                'clone_url': result.get('clone_url', ''),
                                'contributors': contributors,
                                'commit_activity': commit_activity,
                                'weeks': weeks,
                                'metrics': {
                                    'avg_contributions': metrics_accessor_dict.get('avg_contributions', 0),
                                    'active_contributors': metrics_accessor_dict.get('active_contributors', 0),
                                    'open_issues': metrics_accessor_dict.get('open_issues', 0),
                                    'issue_response_time': metrics_accessor_dict.get('issue_response_time', 0),
                                    'total_code': metrics_accessor_dict.get('total_code', 0)
                                },
                                'code_analysis': {
                                    'languages': languages,
                                    'total_code': code_analysis_accessor_dict.get('total_code', 0),
                                    'most_used_language': code_analysis_accessor_dict.get('most_used_language', None),
                                    'ai_analysis': code_analysis_accessor_dict.get('ai_analysis', {
                                        'complexity': 'Unknown',
                                        'important_languages': [],
                                        'technologies': [],
                                        'quality': []
                                    })
                                },
                                'issues': {
                                    'trend': issues_accessor_dict.get('trend', 'Unknown'),
                                    'priorities': issues_accessor_dict.get('priorities', []),
                                    'issues': issues # The processed list of issue dicts
                                }
                            }
                            
                            return render_template('Complete_analise.html',
                                                username=username,
                                                repo_name=repo_name,
                                                result=analysis_result)
                        else:
                            # This part handles other view_types like 'developer'
                            result_data = analysis_service.get_full_analysis(username, repo_name)
                            return render_template('index.html', result=result_data)

                    except Exception as e:
                        error = f"Error generating complete analysis: {str(e)}"
                        print(f"Full error details for complete_analysis action:")
                        import traceback
                        traceback.print_exc()
                        return render_template('index.html', error=error)
                else:
                    result = analysis_service.get_full_analysis(username, repo_name)
                    if view_type == 'developer':
                        return redirect(f'/developer/{username}/{repo_name}')
                    else:
                        return render_template('index.html', result=result)
                    
            except Exception as e:
                error = f"Error processing request: {str(e)}"
                print(f"Full error: {e}")
                return render_template('index.html', error=error)
    
    return render_template('index.html')

@app.route('/developer/<username>/<repo_name>')
def developer_view(username, repo_name):
    try:
        result = analysis_service.get_developer_analysis(username, repo_name)
        return render_template('developer.html', 
                             username=username,
                             repo_name=repo_name,
                             repo_data=result,
                             contributors=result['contributors'],
                             commit_activity=result['commit_activity'],
                             issues=result['issues'])
    except Exception as e:
        error = f"Error processing request: {str(e)}"
        print(f"Full error: {e}")
        return render_template('index.html', error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 
    