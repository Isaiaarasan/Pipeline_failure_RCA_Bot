class LogAgent:
    def __init__(self, ollama_service):
        self.ollama = ollama_service

    def analyze(self, log_content):
        """
        Runs Agent 1: Log Analyzer on the failure log contents.
        Returns a dict containing 'failure_summary' and 'errors'.
        """
        system_prompt = (
            "You are a Senior DevOps and Log Analysis AI Agent.\n"
            "Your task is to read a failed pipeline execution log and analyze the incident.\n"
            "Identify the failure patterns, isolate stack traces, and extract individual error reports.\n\n"
            "You MUST return a JSON object with the following structure. Do NOT include markdown code-block wrappers or any text outside the JSON:\n"
            "{\n"
            "  \"failure_summary\": \"A high-level explanation of what failed and why in the pipeline.\",\n"
            "  \"errors\": [\n"
            "    {\n"
            "      \"error_type\": \"Exception type (e.g., KeyError, ConnectionRefusedError)\",\n"
            "      \"message\": \"Detailed error message\",\n"
            "      \"file\": \"Filename or file path where error originated\",\n"
            "      \"line\": 15,  // Line number as an integer or null\n"
            "      \"stack_trace\": \"Full stack trace or logs leading to the crash\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Please analyze the following pipeline failure log content:\n\n"
            f"--- LOG START ---\n"
            f"{log_content}\n"
            f"--- LOG END ---\n"
        )

        try:
            result = self.ollama.query_agent(system_prompt, user_prompt)
            # Ensure required keys exist
            if not isinstance(result, dict):
                result = {"failure_summary": str(result), "errors": []}
            if "failure_summary" not in result:
                result["failure_summary"] = "Pipeline execution failed with errors."
            if "errors" not in result:
                result["errors"] = []
            return result
        except Exception as e:
            return {
                "failure_summary": f"Failed to execute Log Agent: {str(e)}",
                "errors": []
            }
        
    def get_prompt_metadata(self):
        """
        Returns metadata about this agent's prompts for PROMPTS.md
        """
        return {
            "name": "Agent 1: Log Analyzer",
            "role": "Identify errors, extract stack traces, and synthesize log failures.",
            "prompt_template": "Analyze the log and extract exceptions, messages, lines, and stack traces into JSON format."
        }
