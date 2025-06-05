from typing import Dict, Any, List, Optional, Set
import pandas as pd
from datetime import datetime
import os
import requests
from services.github_service import GitHubService
from services.gemini_service import GeminiService
import re

class AnalysisService:
    def __init__(self):
        self.github_service = GitHubService()
        self.gemini_service = GeminiService()

    def get_full_analysis(self, username: str, repo_name: str) -> Dict[str, Any]:
        """Get complete repository analysis."""
        try:
            repo_data = self.github_service.get_repository(username, repo_name)
            if not isinstance(repo_data, dict):
                print(f"AnalysisService: repo_data is not a dict: {type(repo_data)}")
                repo_data = {}

            contributors = self.github_service.get_contributors(username, repo_name)
            if not isinstance(contributors, list):
                print(f"AnalysisService: contributors is not a list: {type(contributors)}")
                contributors = []

            activity_data = self.github_service.get_commit_activity(username, repo_name)
            if not isinstance(activity_data, dict):
                # get_commit_activity is expected to return a dict or None
                print(f"AnalysisService: activity_data is not a dict: {type(activity_data)}")
                activity_data = {}

            # Process commit activity data
            commit_activity = []
            weeks = []
            if isinstance(activity_data, dict):
                commit_activity = activity_data.get('commit_activity', [])
                weeks = activity_data.get('weeks', [])
            elif isinstance(activity_data, list):
                # If activity_data is a list, use it directly
                commit_activity = activity_data
                # Generate weeks if not provided
                weeks = [f"Week {i+1}" for i in range(len(activity_data))]

            issues_data = self.github_service.get_issues(username, repo_name)
            issues_data_list = issues_data if isinstance(issues_data, list) else []
            
            issues_analysis = self.gemini_service.analyze_issues(issues_data_list)
            if not isinstance(issues_analysis, dict):
                print(f"AnalysisService: issues_analysis from Gemini is not a dict: {type(issues_analysis)}")
                issues_analysis = {'trend': 'N/A', 'priorities': [], 'issues': []}

            readme_content = self.github_service.get_readme(username, repo_name)
            readme_str = readme_content if isinstance(readme_content, str) else ""
            
            # Get repository contents for analysis - FIXED
            contents = self.github_service.get_repository_contents(username, repo_name)
            # Ensure contents is a list
            if not isinstance(contents, list):
                print(f"AnalysisService: contents is not a list: {type(contents)}")
                contents = []
            
            # Analyze code files - FIXED: Pass contents list instead of default_branch
            code_analysis = self._analyze_code_files(username, repo_name, contents)
            
            # Get repository statistics
            stats = self._get_repository_stats(username, repo_name)
            
            # Generate README using the correct method name and parameters
            generated_readme = self.gemini_service.generate_readme(
                repo_data=repo_data if isinstance(repo_data, dict) else {},
                existing_readme=readme_str,
                code_analysis=code_analysis,
                stats=stats
            )
            
            if not isinstance(generated_readme, str):
                print(f"AnalysisService: generated_readme from Gemini is not a str: {type(generated_readme)}")
                generated_readme = "Could not generate README summary."

            # REMOVED THE DUPLICATE CODE ANALYSIS CALL
            # The code_analysis is already calculated above, no need to call it again
            
            metrics = self._calculate_metrics(repo_data, contributors, issues_data_list, activity_data)
            if not isinstance(metrics, dict):
                print(f"AnalysisService: _calculate_metrics did not return a dict: {type(metrics)}")
                metrics = {}

            return {
                'name': repo_data.get('name', '') if isinstance(repo_data, dict) else '',
                'stars': repo_data.get('stargazers_count', 0) if isinstance(repo_data, dict) else 0,
                'forks': repo_data.get('forks_count', 0) if isinstance(repo_data, dict) else 0,
                'watchers': repo_data.get('watchers_count', 0) if isinstance(repo_data, dict) else 0,
                'description': repo_data.get('description', '') if isinstance(repo_data, dict) else '',
                'language': repo_data.get('language', 'Unknown') if isinstance(repo_data, dict) else 'Unknown',
                'clone_url': repo_data.get('clone_url', '') if isinstance(repo_data, dict) else '',
                'contributors': contributors, # Already ensured to be a list
                'commit_activity': commit_activity, # Processed commit activity
                'weeks': weeks, # Processed weeks
                'readme': generated_readme, # Already ensured to be a string
                'issues': issues_analysis, # Already ensured to be a dict
                'code_analysis': code_analysis, # Already ensured to be a dict
                'metrics': metrics # Already ensured to be a dict
            }
        except Exception as e:
            print(f"CRITICAL ERROR in AnalysisService.get_full_analysis for {username}/{repo_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"Internal server error during full analysis: {str(e)}"}

    def get_developer_analysis(self, username: str, repo_name: str) -> Dict[str, Any]:
        """Get developer-focused analysis."""
        analysis = self.get_full_analysis(username, repo_name)
        
        # Add developer-specific metrics
        analysis['developer_metrics'] = {
            'code_quality': self._analyze_code_quality(analysis['code_analysis']),
            'maintenance_score': self._calculate_maintenance_score(analysis),
            'contribution_guidelines': self._generate_contribution_guidelines(analysis)
        }
        
        return analysis

    def generate_readme(self, username: str, repo_name: str) -> Dict[str, Any]:
        """Generate a comprehensive README file."""
        try:
            # 1. Get basic repository data
            repo_data = self.github_service.get_repository(username, repo_name)
            if not repo_data:
                return {'error': 'Failed to fetch repository data'}

            # 2. Get existing README content
            existing_readme = self.github_service.get_readme(username, repo_name)
            
            # 3. Get repository contents for analysis
            contents = self.github_service.get_repository_contents(username, repo_name)
            
            # 4. Analyze all code files
            code_analysis = self._analyze_code_files(username, repo_name, contents)
            
            # 5. Get repository statistics
            stats = self._get_repository_stats(username, repo_name)
            
            # 6. Generate comprehensive README
            readme_content = self.gemini_service.generate_readme(
                repo_data=repo_data,
                existing_readme=existing_readme,
                code_analysis=code_analysis,
                stats=stats
            )
            
            return {
                'readme_content': readme_content,
                'analysis': {
                    'repo_data': repo_data,
                    'code_analysis': code_analysis,
                    'stats': stats
                }
            }
            
        except Exception as e:
            print(f"Error in generate_readme: {str(e)}")
            return {'error': str(e)}

    def _analyze_code_files(self, username: str, repo_name: str, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze all code files in the repository."""
        analysis = {
            'total_files': 0,
            'languages': {},
            'dependencies': set(),
            'main_files': [],
            'architecture': [],
            'complexity': {},
            'total_code': 0,
            'most_used_language': None,
            'ai_analysis': {
                'complexity': 'Unknown',
                'important_languages': [],
                'technologies': [],
                'quality': []
            }
        }
        
        # FIXED: Add type checking and error handling
        if not isinstance(contents, list):
            print(f"AnalysisService._analyze_code_files: contents is not a list: {type(contents)}")
            return analysis
            
        for item in contents:
            # FIXED: Add type checking for each item
            if not isinstance(item, dict):
                print(f"AnalysisService._analyze_code_files: item is not a dict: {type(item)}")
                continue
                
            if item.get('type') == 'file':
                analysis['total_files'] += 1
                
                # Get file content
                content = self.github_service.get_file_content(username, repo_name, item.get('path', ''))
                if content:
                    # Detect language
                    lang = self._detect_language(item.get('path', ''), content)
                    if lang:
                        analysis['languages'][lang] = analysis['languages'].get(lang, 0) + 1
                    
                    # Detect dependencies
                    deps = self._detect_dependencies(content, lang)
                    analysis['dependencies'].update(deps)
                    
                    # Detect main files
                    if self._is_main_file(item.get('path', ''), content):
                        analysis['main_files'].append(item.get('path', ''))
                    
                    # Detect architecture patterns
                    patterns = self._detect_architecture_patterns(content, lang)
                    analysis['architecture'].extend(patterns)
                    
                    # Calculate complexity
                    analysis['complexity'][item.get('path', '')] = self._calculate_complexity(content, lang)
        
        # Calculate total code and most used language
        if analysis['languages']:
            analysis['total_code'] = sum(analysis['languages'].values())
            analysis['most_used_language'] = max(analysis['languages'], key=analysis['languages'].get)
            
            # Update AI analysis
            analysis['ai_analysis'] = {
                'complexity': 'High' if analysis['total_code'] > 50 else 'Medium' if analysis['total_code'] > 10 else 'Low',
                'important_languages': list(analysis['languages'].keys())[:3],
                'technologies': list(analysis['dependencies'])[:5],
                'quality': ['Well-structured' if analysis['total_files'] > 5 else 'Simple structure']
            }
        
        # Convert sets to lists for JSON serialization
        analysis['dependencies'] = list(analysis['dependencies'])
        return analysis

    def _detect_language(self, filename: str, content: str) -> Optional[str]:
        """Detect programming language from file extension and content."""
        if not filename:
            return None
            
        ext = filename.split('.')[-1].lower()
        lang_map = {
            'py': 'Python',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'java': 'Java',
            'cpp': 'C++',
            'c': 'C',
            'go': 'Go',
            'rb': 'Ruby',
            'php': 'PHP',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'rs': 'Rust',
            'md': 'Markdown',
            'html': 'HTML',
            'css': 'CSS',
            'json': 'JSON',
            'yml': 'YAML',
            'yaml': 'YAML',
            'xml': 'XML',
            'sh': 'Shell',
            'ipynb': 'Jupyter Notebook'
        }
        return lang_map.get(ext)

    def _detect_dependencies(self, content: str, lang: Optional[str]) -> Set[str]:
        """Detect dependencies from file content."""
        deps = set()
        if lang == 'Python':
            # Look for import statements
            import_patterns = [
                r'import\s+([a-zA-Z0-9_]+)',
                r'from\s+([a-zA-Z0-9_.]+)\s+import',
                r'pip\s+install\s+([a-zA-Z0-9_\-]+)',
                r'requirements\.txt.*?([a-zA-Z0-9_\-]+)'
            ]
            for pattern in import_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    deps.add(match.group(1))
        return deps

    def _is_main_file(self, filename: str, content: str) -> bool:
        """Determine if a file is a main file based on its name and content."""
        main_indicators = [
            'main', 'app', 'index', 'server', 'init',
            'if __name__ == "__main__"',
            'def main()',
            'public static void main'
        ]
        return any(indicator in filename.lower() or indicator in content for indicator in main_indicators)

    def _detect_architecture_patterns(self, content: str, lang: Optional[str]) -> List[str]:
        """Detect architecture patterns in the code."""
        patterns = []
        if lang == 'Python':
            if 'class' in content:
                patterns.append('Object-Oriented')
            if 'def' in content and 'class' not in content:
                patterns.append('Functional')
            if 'async' in content or 'await' in content:
                patterns.append('Asynchronous')
            if 'flask' in content.lower():
                patterns.append('Web Application')
            if 'tensorflow' in content.lower() or 'torch' in content.lower():
                patterns.append('Machine Learning')
        return patterns

    def _calculate_complexity(self, content: str, lang: Optional[str]) -> Dict[str, int]:
        """Calculate code complexity metrics."""
        complexity = {
            'lines': len(content.splitlines()),
            'functions': len(re.findall(r'def\s+\w+', content)) if lang == 'Python' else 0,
            'classes': len(re.findall(r'class\s+\w+', content)) if lang == 'Python' else 0
        }
        return complexity

    def _get_repository_stats(self, username: str, repo_name: str) -> Dict[str, Any]:
        """Get comprehensive repository statistics."""
        repo_data = self.github_service.get_repository(username, repo_name)
        if not isinstance(repo_data, dict):
            repo_data = {}
            
        return {
            'contributors': self.github_service.get_contributors(username, repo_name),
            'commit_activity': self.github_service.get_commit_activity(username, repo_name),
            'issues': self.github_service.get_issues(username, repo_name),
            'metrics': {
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'open_issues': repo_data.get('open_issues_count', 0)
            }
        }

    def get_code_feedback(self, username: str, repo_name: str) -> Dict[str, Any]:
        """Get code quality feedback."""
        try:
            # Get repository data
            repo_data = self.github_service.get_repository(username, repo_name)
            if not repo_data:
                return {'error': 'Failed to fetch repository data'}

            # Get repository contents
            contents = self.github_service.get_repository_contents(username, repo_name)
            if not contents:
                return {'error': 'Failed to fetch repository contents'}

            # Get README content
            readme_content = self.github_service.get_readme(username, repo_name)

            # Analyze code files
            code_analysis = self._analyze_code_files(username, repo_name, contents)
            
            # Get repository statistics
            stats = self._get_repository_stats(username, repo_name)
            
            # Calculate code quality metrics
            quality_metrics = self._analyze_code_quality(code_analysis)
            
            # Analyze file organization
            file_organization = self._analyze_file_organization(contents)
            
            # Analyze README quality
            readme_quality = self._analyze_readme_quality(readme_content) if readme_content else {
                'score': 0,
                'suggestions': ['No README found. Consider adding a comprehensive README file.']
            }
            
            # Identify improvement areas
            improvement_areas = self._identify_improvement_areas({
                'metrics': stats['metrics'],
                'readme': readme_quality,
                'code_analysis': code_analysis,
                'file_organization': file_organization
            })
            
            # Suggest best practices
            best_practices = self._suggest_best_practices({
                'metrics': stats['metrics'],
                'readme': readme_quality,
                'code_analysis': code_analysis,
                'file_organization': file_organization
            })

            # Calculate overall scores
            code_quality_score = quality_metrics.get('quality_score', 0)
            maintenance_score = self._calculate_maintenance_score({
                'metrics': stats['metrics'],
                'code_analysis': code_analysis
            })
            documentation_score = readme_quality.get('score', 0)

            return {
                'name': repo_data['name'],
                'scores': {
                    'code_quality': code_quality_score,
                    'maintenance': maintenance_score,
                    'documentation': documentation_score
                },
                'structure': file_organization.get('suggestions', []),
                'quality': improvement_areas,
                'documentation': readme_quality.get('suggestions', []),
                'best_practices': best_practices,
                'performance': self._analyze_performance(code_analysis),
                'security': self._analyze_security(code_analysis)
            }
        except Exception as e:
            print(f"Error in get_code_feedback: {str(e)}")
            return {'error': str(e)}

    def _analyze_file_organization(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze file organization and structure."""
        suggestions = []
        file_types = {}
        
        # Ensure contents is a list
        if not isinstance(contents, list):
            return {'suggestions': ['Unable to analyze file organization'], 'file_types': {}}
        
        # Analyze file types and organization
        for item in contents:
            if isinstance(item, dict) and item.get('type') == 'file':
                path = item.get('path', '')
                if path and '.' in path:
                    ext = path.split('.')[-1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
        
        # Check for common organization issues
        if len(file_types) > 10:
            suggestions.append("Consider organizing files into logical directories based on their types")
        
        # Check for configuration files
        config_files = ['config', 'settings', 'env', '.env', 'config.json', 'config.yml']
        if not any(any(cf in item.get('path', '').lower() for cf in config_files) for item in contents if isinstance(item, dict)):
            suggestions.append("Consider adding configuration files for better project setup")
        
        # Check for test files
        test_files = [item for item in contents if isinstance(item, dict) and 'test' in item.get('path', '').lower()]
        if not test_files:
            suggestions.append("Consider adding test files for better code quality")
        
        return {
            'suggestions': suggestions,
            'file_types': file_types
        }

    def _analyze_readme_quality(self, readme_content: str) -> Dict[str, Any]:
        """Analyze README quality and provide suggestions."""
        suggestions = []
        score = 0
        
        if not readme_content:
            return {
                'score': 0,
                'suggestions': ['No README found. Consider adding a comprehensive README file.']
            }
        
        # Check for essential sections
        essential_sections = [
            'installation', 'usage', 'contributing', 'license',
            'description', 'features', 'requirements'
        ]
        
        for section in essential_sections:
            if section.lower() in readme_content.lower():
                score += 10
            else:
                suggestions.append(f"Consider adding a {section} section to your README")
        
        # Check for code examples
        if '```' in readme_content:
            score += 10
        else:
            suggestions.append("Consider adding code examples to your README")
        
        # Check for badges
        if 'badge' in readme_content.lower() or 'shields.io' in readme_content:
            score += 10
        else:
            suggestions.append("Consider adding badges to show project status")
        
        # Check for links
        if 'http' in readme_content:
            score += 10
        else:
            suggestions.append("Consider adding relevant links to your README")
        
        return {
            'score': min(100, score),
            'suggestions': suggestions
        }

    def _analyze_performance(self, code_analysis: Dict[str, Any]) -> List[str]:
        """Analyze code performance and provide suggestions."""
        suggestions = []
        
        # Check for potential performance issues
        if code_analysis.get('total_files', 0) > 100:
            suggestions.append("Consider implementing lazy loading for large files")
        
        if len(code_analysis.get('dependencies', [])) > 20:
            suggestions.append("Review and optimize dependencies to reduce bundle size")
        
        if any('async' in pattern for pattern in code_analysis.get('architecture', [])):
            suggestions.append("Consider implementing caching for async operations")
        
        return suggestions

    def _analyze_security(self, code_analysis: Dict[str, Any]) -> List[str]:
        """Analyze code security and provide suggestions."""
        suggestions = []
        
        # Check for security-related patterns
        if any('api' in dep.lower() for dep in code_analysis.get('dependencies', [])):
            suggestions.append("Implement API key validation and rate limiting")
        
        if any('database' in dep.lower() for dep in code_analysis.get('dependencies', [])):
            suggestions.append("Implement input validation and SQL injection prevention")
        
        if any('web' in pattern.lower() for pattern in code_analysis.get('architecture', [])):
            suggestions.append("Implement CORS and security headers")
        
        return suggestions

    def _calculate_metrics(self, repo_data: Dict, contributors: List[Dict], issues: List[Dict], 
                         activity_data: Dict) -> Dict[str, Any]:
        """Calculate repository metrics."""
        # Ensure repo_data is a dict
        if not isinstance(repo_data, dict):
            repo_data = {}
            
        # Ensure contributors is a list
        if not isinstance(contributors, list):
            contributors = []
            
        # Ensure issues is a list
        if not isinstance(issues, list):
            issues = []
        
        avg_contributions = sum(contrib.get('contributions', 0) for contrib in contributors) / len(contributors) if contributors else 0
        active_contributors = sum(1 for contrib in contributors if contrib.get('contributions', 0) > 10) if contributors else 0
        open_issues = len([issue for issue in issues if isinstance(issue, dict) and issue.get('state') == 'open'])
        
        # Calculate issue response time
        issue_response_time = 7  # Default value
        if issues:
            try:
                issue_dates = pd.to_datetime([issue.get('created_at') for issue in issues if isinstance(issue, dict) and issue.get('created_at')])
                current_time = pd.Timestamp.now(tz='UTC')
                issue_response_time = int((current_time - issue_dates).mean().days)
            except:
                issue_response_time = 7
        
        return {
            'avg_contributions': round(avg_contributions, 2),
            'active_contributors': active_contributors,
            'open_issues': open_issues,
            'issue_response_time': issue_response_time,
            'total_code': 0  # Will be updated by code analysis
        }

    def _analyze_code_quality(self, code_analysis: Dict) -> Dict[str, Any]:
        """Analyze code quality metrics."""
        languages = code_analysis.get('languages', {})
        total_code = sum(languages.values()) if languages else 0
        
        return {
            'complexity': 'Medium' if total_code > 10000 else 'Simple',
            'language_diversity': len(languages),
            'main_language_ratio': max(languages.values()) / total_code if total_code > 0 else 0,
            'quality_score': min(100, int((total_code / 10000) * 50 + (len(languages) * 10)))
        }

    def _calculate_maintenance_score(self, analysis: Dict) -> int:
        """Calculate maintenance score."""
        metrics = analysis.get('metrics', {})
        issues = analysis.get('issues', [])
        
        score = 100
        score -= metrics.get('open_issues', 0) * 2  # Deduct points for open issues
        score -= metrics.get('issue_response_time', 7) * 3  # Deduct points for slow response
        score += metrics.get('active_contributors', 0) * 5  # Add points for active contributors
        
        return max(0, min(100, score))

    def _generate_contribution_guidelines(self, analysis: Dict) -> str:
        """Generate contribution guidelines."""
        return self.gemini_service.generate_content(
            f"""Generate contribution guidelines for this repository:
            Name: {analysis.get('name', 'Unknown')}
            Language: {analysis.get('language', 'Unknown')}
            Active Contributors: {analysis.get('metrics', {}).get('active_contributors', 0)}
            Open Issues: {analysis.get('metrics', {}).get('open_issues', 0)}
            
            Please include:
            1. Setup instructions
            2. Code style guidelines
            3. Pull request process
            4. Testing requirements
            5. Documentation standards
            """
        )

    def _identify_improvement_areas(self, analysis: Dict) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        metrics = analysis.get('metrics', {})
        
        if metrics.get('open_issues', 0) > 10:
            improvements.append("High number of open issues")
        if metrics.get('issue_response_time', 7) > 7:
            improvements.append("Slow issue response time")
        if metrics.get('active_contributors', 0) < 3:
            improvements.append("Limited active contributors")
        if analysis.get('readme', {}).get('score', 0) < 50:
            improvements.append("Documentation needs improvement")
            
        return improvements

    def _suggest_best_practices(self, analysis: Dict) -> List[str]:
        """Suggest best practices."""
        practices = []
        metrics = analysis.get('metrics', {})
        
        if metrics.get('active_contributors', 0) < 3:
            practices.append("Encourage more community contributions")
        if analysis.get('readme', {}).get('score', 0) < 50:
            practices.append("Improve documentation with examples and API references")
        if metrics.get('issue_response_time', 7) > 7:
            practices.append("Implement faster issue response process")
            
        return practices