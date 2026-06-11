import json
import requests
import re
import logging

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self, api_url="http://localhost:11434", model="mistral"):
        self.api_url = api_url.rstrip('/')
        self.model = model

    def check_connection(self):
        """
        Checks if Ollama is reachable and the model is loaded.
        """
        try:
            # First check if Ollama service is running
            response = requests.get(f"{self.api_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models = [m.get("name") for m in response.json().get("models", [])]
                # Check if configured model exists (allowing model name variants e.g. mistral:latest)
                model_exists = any(self.model in m for m in models)
                if not model_exists:
                    logger.warning(f"Ollama is running, but model '{self.model}' was not found in: {models}")
                return response.status_code == 200
            return False
        except Exception:
            return False

    def query_agent(self, system_prompt, user_prompt):
        """
        Queries Ollama model with system and user prompts.
        Forces JSON output format and attempts to parse it.
        """
        if not self.check_connection():
            logger.error(f"Ollama not running or unreachable at {self.api_url} with model {self.model}.")
            raise ConnectionError(f"Ollama is unreachable or model '{self.model}' is not loaded.")

        url = f"{self.api_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=45)
            if response.status_code != 200:
                logger.error(f"Ollama returned error status {response.status_code}: {response.text}")
                raise RuntimeError(f"Ollama API error: {response.text}")

            data = response.json()
            message_content = data.get("message", {}).get("content", "")
            return self._parse_json_response(message_content)

        except Exception as e:
            logger.error(f"Failed to query Ollama API: {str(e)}")
            raise e

    def _parse_json_response(self, text):
        """
        Robustly extracts and parses JSON content from LLM response text,
        handling possible markdown block formatting wrapper.
        """
        cleaned = text.strip()
        # Remove markdown code fence wrapper if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from Ollama response. Raw: {text}. Error: {e}")
            # Try to pull out something using regex as a last resort
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            raise ValueError("Ollama response could not be parsed as JSON")

    def _estimate_fallback_severity_confidence(self, text):
        """Estimate severity and confidence from the log text when Ollama is unavailable."""
        normalized = text.lower()

        critical_keywords = [
            "fatal", "panic", "segfault", "core dumped", "out of memory",
            "permission denied", "access denied", "disk full", "unhandled exception",
            "data loss", "stack overflow", "critical error", "traceback",
            "keyerror", "nullpointer", "indexerror", "runtimeerror", "exception"
        ]
        high_keywords = [
            "connection refused", "failed to connect", "database error", "could not connect",
            "connection timeout", "timeout", "authentication failed", "permission denied",
            "service unavailable", "502", "503", "504", "broken pipe", "unreachable"
        ]
        medium_keywords = [
            "warning", "deprecated", "slow", "retry", "retrying", "timeout warning",
            "limited", "throttled", "rate limit", "cache miss", "retry attempt"
        ]

        if any(k in normalized for k in critical_keywords):
            return "Critical", "90%"
        if any(k in normalized for k in high_keywords):
            return "High", "80%"
        if any(k in normalized for k in medium_keywords):
            return "Medium", "65%"
        return "Low", "50%"

    def _simulate_agent_fallback(self, system_prompt, user_prompt):
        """
        A rule-based simulation engine that creates highly context-aware response payloads
        by analyzing inputs for keywords (like KeyError, db_config, timestamp, diffs, commits).
        """
        user_prompt_lower = user_prompt.lower()
        
        # 1. Identify which Agent is calling based on prompt keyword patterns
        if "log analyzer" in system_prompt.lower() or "extract errors" in system_prompt.lower():
            # AGENT 1 fallback
            errors = []
            failure_summary = "An ETL pipeline failure was detected."
            
            if "keyerror: 'timestamp'" in user_prompt_lower or "keyerror" in user_prompt_lower:
                errors = [
                    {
                        "error_type": "KeyError",
                        "message": "'timestamp'",
                        "file": "pipeline/handler.py",
                        "line": 15,
                        "stack_trace": "Traceback (most recent call):\\n  File \\\"etl_job.py\\\", line 42, in run\\n    formatted = format_payload(row)\\n  File \\\"pipeline/handler.py\\\", line 15, in format_payload\\n    payload['timestamp'] = raw_data['timestamp']\\nKeyError: 'timestamp'"
                    }
                ]
                failure_summary = "The ETL pipeline crashed with a KeyError exception due to a missing 'timestamp' key in the database row record payload."
            elif "connection refused" in user_prompt_lower or "postgresql" in user_prompt_lower:
                errors = [
                    {
                        "error_type": "OperationalError",
                        "message": "could not connect to server: Connection refused",
                        "file": "database.py",
                        "line": 88,
                        "stack_trace": "sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server: Connection refused\\n  Is the server running on host \\\"localhost\\\" (127.0.0.1) and accepting TCP/IP connections on port 5432?"
                    }
                ]
                failure_summary = "The database connection failed. The application was unable to establish a connection to PostgreSQL on port 5432."
            else:
                errors = [
                    {
                        "error_type": "UnknownPipelineError",
                        "message": "ETL pipeline execution interrupted unexpectedly",
                        "file": "run_pipeline.py",
                        "line": 204,
                        "stack_trace": "Error: Pipeline run failed during batch write step."
                    }
                ]
                failure_summary = "The pipeline run failed due to a general exception during batch data execution."

            return {
                "failure_summary": failure_summary,
                "errors": errors
            }

        elif "github analyzer" in system_prompt.lower() or "suspicious code changes" in system_prompt.lower():
            # AGENT 2 fallback
            if "format_payload" in user_prompt or "pipeline/handler.py" in user_prompt or "ts" in user_prompt:
                return {
                    "commit_id": "8c7a2b9f3d1e4e5f6a7b8c9d0e1f2a3b4c5d6e7f",
                    "changed_files": ["pipeline/handler.py", "tests/test_handler.py"],
                    "diff_summary": "Commit 8c7a2b9f modified pipeline/handler.py by renaming dictionary key 'timestamp' to 'ts' (formatted['ts'] = raw_data.get('created_at')). This directly impacts files reading key 'timestamp'."
                }
            elif "pool_size" in user_prompt or "config/db_config.json" in user_prompt:
                return {
                    "commit_id": "4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b",
                    "changed_files": ["config/db_config.json"],
                    "diff_summary": "Commit 4a5b6c7d updated the database pool size and connections configurations in db_config.json."
                }
            else:
                return {
                    "commit_id": "8c7a2b9f3d1e4e5f6a7b8c9d0e1f2a3b4c5d6e7f",
                    "changed_files": ["pipeline/handler.py"],
                    "diff_summary": "Commit 8c7a2b9f modified pipeline files, changing schema format keys."
                }

        else:
            # AGENT 3 fallback: RCA GENERATOR

            if "keyerror" in user_prompt_lower or "timestamp" in user_prompt_lower:
                return {
                    "root_cause": "The pipeline failed due to a KeyError exception: 'timestamp' in pipeline/handler.py at line 15. This was directly introduced in commit 8c7a2b9f3d1e4e5f6a7b8c9d0e1f2a3b4c5d6e7f ('Refactor dictionary response keys in ETL payload formatting') by dev-engineer-lead. The commit changed the payload mapping keys to use 'ts' instead of 'timestamp', but downstream database loader script still expects the 'timestamp' key, leading to a crash when it tries to extract 'timestamp' from the payload dictionary.",
                    "confidence_score": "95%",
                    "severity": "Critical",
                    "recommendation": "Update the downstream database loader code in etl_job.py to expect 'ts' instead of 'timestamp', or revert the dictionary key change in pipeline/handler.py to maintain backward compatibility.",
                    "retry_steps": "1. Revert commit 8c7a2b9f or apply hotfix to pipeline/handler.py.\\n2. Run local tests (pytest tests/test_handler.py) to confirm formatting structure.\\n3. Push fix to main repository.\\n4. Trigger pipeline rerun via standard workflow."
                }
            elif "connection refused" in user_prompt_lower or "database" in user_prompt_lower:
                return {
                    "root_cause": "The ETL job failed to connect to the PostgreSQL instance at localhost:5432. The database service is either down, or firewalled, or connection parameters in the environment configuration were changed, leading to Connection Refused.",
                    "confidence_score": "90%",
                    "severity": "High",
                    "recommendation": "Check if the PostgreSQL database is running on localhost:5432. Verify credentials in environmental configurations and ensure the security group rules allow traffic.",
                    "retry_steps": "1. Run 'pg_ctl status' or check Docker container status to ensure postgres service is active.\\n2. Verify local connectivity using psql: 'psql -h localhost -U postgres'.\\n3. Restart pipeline worker after confirming database is active."
                }
            else:
                return {
                    "root_cause": "The pipeline crashed during raw batch processing. Commits show recent changes in files but no obvious correlation. The error points to environment configurations or network latency.",
                    "confidence_score": "60%",
                    "severity": "Medium",
                    "recommendation": "Examine the worker memory profiles and database execution times. Increase execution timeout settings in pipeline configuration.",
                    "retry_steps": "1. Check server metrics for out of memory (OOM) alerts.\\n2. Clear pipeline temp locks.\\n3. Restart pipeline runner."
                }

            severity, confidence_score = self._estimate_fallback_severity_confidence(user_prompt_lower)

            if severity == "Critical":
                root_cause = (
                    "The pipeline failed due to a severe runtime exception or system failure. "
                    "This condition is critical and must be addressed immediately to restore pipeline stability."
                )
            elif severity == "High":
                root_cause = (
                    "The ETL job encountered a significant failure such as database connectivity or service unavailability. "
                    "This issue is high-impact and can stop the pipeline from completing successfully."
                )
            elif severity == "Medium":
                root_cause = (
                    "The pipeline execution encountered a recoverable or degraded condition such as retries, warnings, or performance issues. "
                    "This should be investigated but is less likely to be a full outage."
                )
            else:
                root_cause = (
                    "The pipeline log indicates a lower-impact issue or an informational condition. "
                    "This is likely a minor configuration or environment discrepancy and should be verified."
                )

            return {
                "root_cause": root_cause,
                "confidence_score": confidence_score,
                "severity": severity,
                "recommendation": "Investigate the reported pipeline condition and apply an appropriate fix based on the log context.",
                "retry_steps": "1. Review the pipeline output and configuration.\n2. Adjust any environment or connection settings.\n3. Re-run the pipeline after correcting the issue."
            }

