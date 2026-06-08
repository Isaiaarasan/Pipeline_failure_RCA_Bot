import os
import sys
# Ensure project root is on sys.path so local imports work when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
import models
from services.db_service import DBService, MongoDoc
from services.github_service import GitHubService
from services.ollama_service import OllamaService
from agents.log_agent import LogAgent
from agents.github_agent import GitHubAgent
from agents.rca_agent import RCAAgent
from services.pdf_service import PDFService
import os

def run_latest_failure_analysis():
    # Initialize DB (will fallback to mock if unreachable)
    models.init_db(Config.MONGODB_URI)

    # Fetch latest failure log (robust to mock lists/cursors)
    results_cursor = models.db.logs.find({'log_type': 'failure'}, sort=[('uploaded_at', -1)])
    try:
        if hasattr(results_cursor, 'limit'):
            results = list(results_cursor.limit(1))
        else:
            results = list(results_cursor)[:1]
    except Exception:
        results = list(results_cursor)[:1]

    if not results:
        uploaded_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'error.log'))
        if os.path.exists(uploaded_path):
            print(f"No DB failure logs found. Loading real uploaded failure file: {uploaded_path}")
            with open(uploaded_path, 'r', encoding='utf-8', errors='ignore') as f:
                uploaded_content = f.read()
            sample_log = DBService.save_log(filename='error.log', log_type='failure', content=uploaded_content)
            results = [sample_log._data]
        else:
            print("No failure logs found. Creating a sample failure log for demo...")
            sample_content = (
                "Traceback (most recent call last):\n"
                "  File \"etl_job.py\", line 42, in run\n"
                "    formatted = format_payload(row)\n"
                "  File \"pipeline/handler.py\", line 15, in format_payload\n"
                "    payload['timestamp'] = raw_data['timestamp']\n"
                "KeyError: 'timestamp'\n"
            )
            sample_log = DBService.save_log(filename='sample_failure.log', log_type='failure', content=sample_content)
            results = [sample_log._data]

    failed_log = MongoDoc(results[0])
    print(f"Found failure log id={failed_log.id}, filename={failed_log.filename}")

    # Get latest success log
    success_log = DBService.get_latest_success_log()

    # Fetch commits (mock if not configured)
    gh_service = GitHubService(token=Config.GITHUB_TOKEN, repo=Config.GITHUB_REPO)
    commits = gh_service.fetch_recent_commits(limit=5)

    # Initialize Ollama/Agents
    ollama = OllamaService(api_url=Config.OLLAMA_API_URL, model=Config.OLLAMA_MODEL)
    log_agent = LogAgent(ollama)
    github_agent = GitHubAgent(ollama)
    rca_agent = RCAAgent(ollama)

    print("Running Log Agent...")
    log_analysis = log_agent.analyze(failed_log.content)
    print("Log analysis done:", log_analysis.get('failure_summary'))

    print("Running GitHub Agent...")
    github_analysis = github_agent.analyze(commits, log_analysis.get('errors', []))
    print("GitHub analysis done: commit", github_analysis.get('commit_id'))

    print("Saving GitHub analysis to DB...")
    db_gh = DBService.save_github_analysis(
        commit_id=github_analysis.get('commit_id'),
        changed_files=github_analysis.get('changed_files'),
        diff_summary=github_analysis.get('diff_summary')
    )

    print("Running RCA Agent...")
    rca_result = rca_agent.analyze(log_analysis, github_analysis, success_log.content if success_log else None)
    print("RCA generation done. Confidence:", rca_result.get('confidence_score'))

    print("Saving report to DB...")
    report = DBService.save_report(
        failure_summary=log_analysis.get('failure_summary', 'Pipeline failed execution.'),
        root_cause=rca_result.get('root_cause'),
        severity=rca_result.get('severity'),
        confidence_score=rca_result.get('confidence_score'),
        recommendation=rca_result.get('recommendation'),
        retry_steps=rca_result.get('retry_steps'),
        log_id=failed_log.id,
        github_analysis_id=db_gh.id
    )

    print(f"Report saved with id={report.id}")

    # Generate PDF and save locally
    try:
        pdf_buf = PDFService.generate_rca_pdf(report)
        out_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), f"../uploads/RCA_Report_{report.id:04d}.pdf")
        out_path = os.path.abspath(out_path)
        with open(out_path, 'wb') as f:
            f.write(pdf_buf.getvalue())
        print(f"PDF exported to: {out_path}")
    except Exception as e:
        print(f"Failed to generate PDF: {e}")

    # Print concise report summary
    print("--- RCA SUMMARY ---")
    print("Report ID:", report.id)
    print("Failure Summary:", report.failure_summary)
    print("Root Cause:", report.root_cause)
    print("Severity:", report.severity)
    print("Confidence:", report.confidence_score)
    print("Recommendation:", report.recommendation)

    return report

if __name__ == '__main__':
    run_latest_failure_analysis()
