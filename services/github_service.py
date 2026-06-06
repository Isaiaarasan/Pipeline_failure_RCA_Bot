import requests
import logging

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, token=None, repo=None):
        self.token = token
        self.repo = repo
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def is_configured(self):
        return bool(self.token and self.repo)

    def fetch_recent_commits(self, limit=5):
        """
        Fetches recent commits and their diff details from the GitHub repository.
        If config is missing or request fails, returns mock data for demonstration.
        """
        if not self.is_configured():
            logger.warning("GitHub integration not fully configured. Using mock commit data.")
            return self._get_mock_commits()

        url = f"https://api.github.com/repos/{self.repo}/commits"
        params = {"per_page": limit}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch commits from GitHub (Status {response.status_code}): {response.text}")
                return self._get_mock_commits()
                
            commits_list = response.json()
            detailed_commits = []
            
            for c in commits_list[:limit]:
                sha = c.get("sha")
                commit_details = self.fetch_commit_detail(sha)
                if commit_details:
                    detailed_commits.append(commit_details)
                else:
                    # Fallback to basic info if detail fetch failed
                    detailed_commits.append({
                        "commit_id": sha,
                        "author": c.get("commit", {}).get("author", {}).get("name", "Unknown"),
                        "date": c.get("commit", {}).get("author", {}).get("date", ""),
                        "message": c.get("commit", {}).get("message", ""),
                        "changed_files": [],
                        "diff_summary": "Diff details unavailable."
                    })
            return detailed_commits

        except Exception as e:
            logger.error(f"Error connecting to GitHub API: {str(e)}")
            return self._get_mock_commits()

    def fetch_commit_detail(self, sha):
        """
        Fetches detailed information for a specific commit, including list of changed files and diffs.
        """
        url = f"https://api.github.com/repos/{self.repo}/commits/{sha}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None
                
            data = response.json()
            changed_files = []
            diffs = []
            
            for file_info in data.get("files", []):
                filename = file_info.get("filename")
                changed_files.append(filename)
                
                patch = file_info.get("patch", "")
                if patch:
                    diffs.append(f"--- a/{filename}\n+++ b/{filename}\n{patch}")
            
            return {
                "commit_id": sha,
                "author": data.get("commit", {}).get("author", {}).get("name", "Unknown"),
                "date": data.get("commit", {}).get("author", {}).get("date", ""),
                "message": data.get("commit", {}).get("message", ""),
                "changed_files": changed_files,
                "diff_summary": "\n\n".join(diffs)
            }
        except Exception as e:
            logger.error(f"Error fetching commit details for {sha}: {str(e)}")
            return None

    def _get_mock_commits(self):
        """
        Returns realistic mock commit history simulating a recent regression
        (e.g., changing dictionary keys, causing a KeyError in a database ETL job).
        """
        return [
            {
                "commit_id": "8c7a2b9f3d1e4e5f6a7b8c9d0e1f2a3b4c5d6e7f",
                "author": "dev-engineer-lead",
                "date": "2026-06-06T18:45:00Z",
                "message": "Refactor dictionary response keys in ETL payload formatting",
                "changed_files": ["pipeline/handler.py", "tests/test_handler.py"],
                "diff_summary": """--- a/pipeline/handler.py
+++ b/pipeline/handler.py
@@ -12,8 +12,8 @@
 def format_payload(raw_data):
     # Restructuring keys for compatibility with API v2
     formatted = {}
-    formatted['timestamp'] = raw_data.get('created_at')
-    formatted['record_id'] = raw_data.get('id')
+    formatted['ts'] = raw_data.get('created_at')  # Renamed key to 'ts'
+    formatted['id'] = raw_data.get('id')
     formatted['payload_type'] = 'etl_event'
     return formatted
"""
            },
            {
                "commit_id": "4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b",
                "author": "data-ops-engineer",
                "date": "2026-06-05T12:30:00Z",
                "message": "Update database pool config and connection retries",
                "changed_files": ["config/db_config.json"],
                "diff_summary": """--- a/config/db_config.json
+++ b/config/db_config.json
@@ -4,5 +4,5 @@
   "port": 5432,
-  "pool_size": 5,
-  "max_overflow": 10
+  "pool_size": 10,
+  "max_overflow": 20,
+  "connection_timeout": 30
 }
"""
            }
        ]
