import json

class RCAAgent:
    ALLOWED_SEVERITIES = ["Critical", "High", "Medium", "Low"]

    def __init__(self, ollama_service):
        self.ollama = ollama_service

    def _normalize_severity(self, severity, failure_summary=None, errors=None):
        """Normalize severity output to one of the allowed severity levels."""
        if isinstance(severity, str):
            cleaned = severity.strip().lower()
            for level in self.ALLOWED_SEVERITIES:
                if cleaned == level.lower():
                    return level
            for level in self.ALLOWED_SEVERITIES:
                if level.lower() in cleaned:
                    return level

        text = []
        if failure_summary:
            text.append(str(failure_summary))
        if isinstance(errors, list):
            for error in errors:
                if isinstance(error, dict):
                    text.append(error.get('error_type', ''))
                    text.append(error.get('message', ''))
                    text.append(error.get('stack_trace', ''))
                else:
                    text.append(str(error))
        combined = " ".join([t.lower() for t in text if t])

        critical_keywords = ["fatal", "panic", "segfault", "core dumped", "out of memory", "permission denied", "access denied", "disk full", "unhandled exception", "data loss", "stack overflow", "critical error", "traceback"]
        high_keywords = ["connection refused", "failed to connect", "timeout", "cannot connect", "connection timeout", "database error", "error", "exception"]
        medium_keywords = ["warning", "deprecated", "slow", "retry", "retrying", "timeout warning", "limited", "throttled"]

        if any(k in combined for k in critical_keywords):
            return "Critical"
        if any(k in combined for k in high_keywords):
            return "High"
        if any(k in combined for k in medium_keywords):
            return "Medium"
        return "Low"

    def _adjust_severity_for_confidence(self, severity, confidence_score):
        """Adjust severity based on the confidence score thresholds.

        Rules:
        - Critical should only remain Critical if confidence > 80
        - High should only remain High if confidence > 70
        - Medium should only remain Medium if confidence > 55
        - Otherwise downgrade to Low
        """
        try:
            if isinstance(confidence_score, str):
                conf_value = float(confidence_score.replace('%', '').strip())
            else:
                conf_value = float(confidence_score)
        except Exception:
            return severity

        if conf_value > 80:
            if severity == "Critical":
                return "Critical"
            return severity
        if conf_value > 70:
            if severity == "Critical":
                return "High"
            if severity == "High":
                return "High"
            return severity
        if conf_value > 55:
            if severity in ("Critical", "High"):
                return "Medium"
            if severity == "Medium":
                return "Medium"
            return "Low"
        return "Low"

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

            result["severity"] = self._normalize_severity(
                result.get("severity"),
                failure_summary=log_analysis.get("failure_summary"),
                errors=log_analysis.get("errors")
            )
            result["severity"] = self._adjust_severity_for_confidence(
                result["severity"],
                result.get("confidence_score")
            )
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
