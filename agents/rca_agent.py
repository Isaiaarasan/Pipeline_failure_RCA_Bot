import json

class RCAAgent:
    def __init__(self, ollama_service):
        self.ollama = ollama_service

    def analyze(self, log_analysis, github_analysis, success_log_content=None):
        """
        Runs Agent 3: RCA Generator.
        Synthesizes log analysis, github correlation, and historical success details
        into a final root cause report.
        Returns a dict containing 'root_cause', 'confidence_score', 'severity',
        'recommendation', and 'retry_steps'.
        """
        system_prompt = (
            "You are a Senior Principal DevOps Architect and RCA AI Agent.\n"
            "Your task is to synthesize the findings from a failure log analysis and a code change audit,\n"
            "comparing them with the last successful pipeline log if available.\n"
            "Produce the final Root Cause Analysis (RCA) report.\n\n"
            "You MUST return a JSON object with the exact following structure. Do NOT include markdown code-block wrappers or any text outside the JSON:\n"
            "{\n"
            "  \"root_cause\": \"A detailed technical narrative explaining the exact failure, how it occurred, and connecting it to any code changes that introduced it.\",\n"
            "  \"confidence_score\": \"A percentage estimating your certainty (e.g., '90%')\",\n"
            "  \"severity\": \"Severity level classification: 'Critical', 'High', 'Medium', or 'Low'\",\n"
            "  \"recommendation\": \"Detailed, actionable code/configuration fix recommendation for developer remediation.\",\n"
            "  \"retry_steps\": \"Numbered list of steps to clean up data, patch, and re-run/retry the pipeline.\"\n"
            "}"
        )

        success_context = success_log_content if success_log_content else "No previous successful log is available for comparison."

        user_prompt = (
            f"--- 1. FAILED LOG ANALYSIS ---\n"
            f"{json.dumps(log_analysis, indent=2)}\n\n"
            f"--- 2. GITHUB SUSPICIOUS CHANGES ---\n"
            f"{json.dumps(github_analysis, indent=2)}\n\n"
            f"--- 3. LAST SUCCESSFUL LOG REFERENCE ---\n"
            f"{success_context}\n\n"
            f"Please synthesize this information and write the final root cause analysis report."
        )

        try:
            result = self.ollama.query_agent(system_prompt, user_prompt)
            # Ensure required keys exist
            if not isinstance(result, dict):
                result = {
                    "root_cause": str(result),
                    "confidence_score": "50%",
                    "severity": "Medium",
                    "recommendation": "Review logs and code edits.",
                    "retry_steps": "1. Review logs.\n2. Run manually."
                }
            if "root_cause" not in result:
                result["root_cause"] = "Unknown root cause."
            if "confidence_score" not in result:
                result["confidence_score"] = "50%"
            if "severity" not in result:
                result["severity"] = "Medium"
            if "recommendation" not in result:
                result["recommendation"] = "Review the failure and correlated diffs."
            if "retry_steps" not in result:
                result["retry_steps"] = "1. Clean up.\n2. Rerun."
            return result
        except Exception as e:
            return {
                "root_cause": f"Failed to execute RCA Agent: {str(e)}",
                "confidence_score": "0%",
                "severity": "High",
                "recommendation": "Check application log files.",
                "retry_steps": "1. Check database connection.\n2. Rerun manually."
            }

    def get_prompt_metadata(self):
        """
        Returns metadata about this agent's prompts for PROMPTS.md
        """
        return {
            "name": "Agent 3: RCA Generator",
            "role": "Synthesize log reports, historical success logs, and git audits to write final reports.",
            "prompt_template": "Compare failed analysis, GitHub changes, and successful log context to output RCA, severity, confidence, recommendation, and retry steps in JSON format."
        }
