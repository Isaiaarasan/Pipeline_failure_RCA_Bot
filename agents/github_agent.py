import json

class GitHubAgent:
    def __init__(self, ollama_service):
        self.ollama = ollama_service

    def analyze(self, commits_data, errors_data):
        """
        Runs Agent 2: GitHub Analyzer.
        Analyzes recent commits/diffs and correlates them with the log errors.
        Returns a dict containing 'commit_id', 'changed_files', and 'diff_summary'.
        """
        system_prompt = (
            "You are a Senior DevOps and Git Code Auditor AI Agent.\n"
            "Your task is to analyze recent GitHub commits, changed files, and git diffs,\n"
            "correlating them with the pipeline crash errors provided.\n"
            "Identify the single most suspicious commit and explain how its changes match or could have caused the errors.\n\n"
            "You MUST return a JSON object with the exact following structure. Do NOT include markdown code-block wrappers or any text outside the JSON:\n"
            "{\n"
            "  \"commit_id\": \"The SHA hash of the most suspicious commit (empty if none match)\",\n"
            "  \"changed_files\": [\"list\", \"of\", \"suspicious\", \"files\", \"changed\"],\n"
            "  \"diff_summary\": \"Explanation of why this commit is suspicious and how its changes correlate with the errors.\"\n"
            "}"
        )

        user_prompt = (
            f"Here are the errors extracted from the pipeline crash:\n"
            f"{json.dumps(errors_data, indent=2)}\n\n"
            f"Here are the recent GitHub commits and their code diffs:\n"
            f"{json.dumps(commits_data, indent=2)}\n\n"
            f"Please correlate the commits with the error reports and determine which commit is the likely root cause."
        )

        try:
            result = self.ollama.query_agent(system_prompt, user_prompt)
            # Ensure required keys exist
            if not isinstance(result, dict):
                result = {"commit_id": "", "changed_files": [], "diff_summary": str(result)}
            if "commit_id" not in result:
                result["commit_id"] = ""
            if "changed_files" not in result:
                result["changed_files"] = []
            if "diff_summary" not in result:
                result["diff_summary"] = "No obvious matching code changes found correlating with the error."
            return result
        except Exception as e:
            return {
                "commit_id": "",
                "changed_files": [],
                "diff_summary": f"Failed to execute GitHub Agent: {str(e)}"
            }
        
    def get_prompt_metadata(self):
        """
        Returns metadata about this agent's prompts for PROMPTS.md
        """
        return {
            "name": "Agent 2: GitHub Analyzer",
            "role": "Correlate commit diffs with active logs stack trace files to flag regressions.",
            "prompt_template": "Examine commits and diff files, check error files, and return suspicious commit metadata in JSON format."
        }
