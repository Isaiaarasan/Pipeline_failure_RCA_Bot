# Test Cases: Pipeline Failure RCA Bot

## Functional Testing

| Test ID | Module | Scenario | Steps to Execute | Expected Result | Pass/Fail |
|---|---|---|---|---|---|
| TC-001 | File Upload | Upload a valid success log | 1. Go to dashboard<br>2. Select "Success Log"<br>3. Upload `success_pipeline.log` | File uploads successfully, no RCA is triggered, saved to database. | |
| TC-002 | File Upload | Upload a valid failure log | 1. Go to dashboard<br>2. Select "Failure Log"<br>3. Upload `failed_pipeline.log` | File uploads, triggers the AI RCA pipeline immediately. | |
| TC-003 | Analysis Pipeline | Trigger full RCA | 1. Upload a failure log.<br>2. Wait for loading screen. | System redirects to the RCA Report page. Report contains Root Cause, Severity, Confidence, and Retry Steps. | |
| TC-004 | PDF Export | Export RCA to PDF | 1. Open a generated RCA report.<br>2. Click "Export PDF". | Browser downloads a formatted `.pdf` containing the incident details. | |
| TC-005 | History Dashboard | View previous reports | 1. Click on the "History" or Dashboard tab. | A list of all historical analyses appears, matching the data in MongoDB. | |

## Non-Functional & AI Fallback Testing

| Test ID | Module | Scenario | Steps to Execute | Expected Result | Pass/Fail |
|---|---|---|---|---|---|
| TC-006 | AI Resilience | Ollama is Offline | 1. Stop local Ollama server.<br>2. Upload `failed_pipeline.log` with `KeyError: 'timestamp'` | System gracefully falls back to the simulator. A structured report is generated indicating the dictionary key change without crashing. | |
| TC-007 | AI Resilience | Database Timeout Log | 1. Upload `db_timeout.log` | The RCA Generator identifies it as a High severity network/database issue and recommends checking port 5432. | |
| TC-008 | Data Integrity | Invalid File Type | 1. Upload an image `.png` instead of a `.log` or `.txt`. | System rejects the upload with an error message indicating invalid file format. | |

## Database Integration Testing

| Test ID | Module | Scenario | Steps to Execute | Expected Result | Pass/Fail |
|---|---|---|---|---|---|
| TC-009 | MongoDB Sync | Verify data persistence | 1. Generate a new report.<br>2. Restart the Flask Server.<br>3. Go to Dashboard. | The generated report is still visible in the dashboard, proving MongoDB persistence. | |
| TC-010 | Database Offline | MongoDB is Offline | 1. Stop MongoDB service.<br>2. Start Flask app. | App should either fail gracefully on startup or log a specific ConnectionFailure timeout error. | |
