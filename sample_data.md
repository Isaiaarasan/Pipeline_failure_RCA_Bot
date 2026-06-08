# Sample Data for Testing

You can save these blocks into `.log` files to upload into the application and demonstrate its capabilities.

## 1. Failed Log: `failed_pipeline.log`
This log demonstrates a Python KeyError during an ETL batch job, which perfectly triggers the AI and fallback simulators.

```text
2026-06-08 00:15:01 - INFO - [ETL_PIPELINE] Starting daily batch job for user_events...
2026-06-08 00:15:02 - INFO - [ETL_PIPELINE] Connecting to source database...
2026-06-08 00:15:05 - INFO - [ETL_PIPELINE] Fetched 150,000 records. Beginning transformation...
2026-06-08 00:15:10 - ERROR - [ETL_PIPELINE] Transformation failed on record batch 3.
Traceback (most recent call):
  File "etl_job.py", line 42, in run
    formatted = format_payload(row)
  File "pipeline/handler.py", line 15, in format_payload
    payload['timestamp'] = raw_data['timestamp']
KeyError: 'timestamp'
2026-06-08 00:15:10 - CRITICAL - [ETL_PIPELINE] Job aborted due to fatal error.
```

## 2. Success Log: `success_pipeline.log`
This log represents the baseline of a healthy run, which the RCA Generator (Agent 3) uses for comparison.

```text
2026-06-07 00:15:00 - INFO - [ETL_PIPELINE] Starting daily batch job for user_events...
2026-06-07 00:15:02 - INFO - [ETL_PIPELINE] Connecting to source database...
2026-06-07 00:15:06 - INFO - [ETL_PIPELINE] Fetched 148,200 records. Beginning transformation...
2026-06-07 00:16:45 - INFO - [ETL_PIPELINE] Transformation successful. Loading into target warehouse...
2026-06-07 00:18:12 - INFO - [ETL_PIPELINE] Data loaded successfully.
2026-06-07 00:18:13 - INFO - [ETL_PIPELINE] Job completed without errors.
```

## 3. Database Connection Failure Log: `db_timeout.log`
Use this log to demonstrate the `ConnectionRefused` scenario.

```text
2026-06-08 12:00:01 - INFO - [ETL_PIPELINE] Starting synchronization task...
2026-06-08 12:00:01 - INFO - [ETL_PIPELINE] Attempting to connect to PostgreSQL at localhost:5432...
2026-06-08 12:00:31 - ERROR - [ETL_PIPELINE] Database connection timed out.
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server: Connection refused
  Is the server running on host "localhost" (127.0.0.1) and accepting TCP/IP connections on port 5432?
2026-06-08 12:00:31 - CRITICAL - [ETL_PIPELINE] Halting execution.
```
