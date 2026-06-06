from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from models import db
from services.db_service import DBService, MongoDoc
from services.github_service import GitHubService
from services.ollama_service import OllamaService
from agents.log_agent import LogAgent
from agents.github_agent import GitHubAgent
from agents.rca_agent import RCAAgent

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analyze', methods=['GET'])
def analyze():
    # 1. Get the failed log ID to analyze
    log_id = request.args.get('log_id', type=int)
    
    if log_id:
        log_data = db.logs.find_one({'_id': log_id})
        failed_log = MongoDoc(log_data) if log_data else None
    else:
        # Fallback to the latest uploaded failure log
        results = list(db.logs.find({'log_type': 'failure'}, sort=[('uploaded_at', -1)]).limit(1))
        failed_log = MongoDoc(results[0]) if results else None
        
    if not failed_log:
        flash("No failure logs found. Please upload a failed pipeline log to begin analysis.", "warning")
        return redirect(url_for('upload.upload_log'))

    try:
        # 2. Load the latest successful log
        success_log = DBService.get_latest_success_log()
        success_content = success_log.content if success_log else None

        # 3. Fetch GitHub data
        gh_service = GitHubService(
            token=current_app.config['GITHUB_TOKEN'],
            repo=current_app.config['GITHUB_REPO']
        )
        commits_data = gh_service.fetch_recent_commits(limit=5)

        # 4. Initialize Ollama Service and Agents
        ollama_service = OllamaService(
            api_url=current_app.config['OLLAMA_API_URL'],
            model=current_app.config['OLLAMA_MODEL']
        )
        
        log_agent = LogAgent(ollama_service)
        github_agent = GitHubAgent(ollama_service)
        rca_agent = RCAAgent(ollama_service)

        # Step A: Run Log Analyzer (Agent 1)
        log_analysis = log_agent.analyze(failed_log.content)

        # Step B: Run GitHub Analyzer (Agent 2)
        github_analysis_result = github_agent.analyze(commits_data, log_analysis.get('errors', []))

        # Save Github analysis to database
        db_gh_analysis = DBService.save_github_analysis(
            commit_id=github_analysis_result.get('commit_id'),
            changed_files=github_analysis_result.get('changed_files'),
            diff_summary=github_analysis_result.get('diff_summary')
        )

        # Step C: Run RCA Generator (Agent 3)
        rca_report_result = rca_agent.analyze(
            log_analysis=log_analysis,
            github_analysis=github_analysis_result,
            success_log_content=success_content
        )

        # 5. Save report in DB
        report = DBService.save_report(
            failure_summary=log_analysis.get('failure_summary', 'Pipeline failed execution.'),
            root_cause=rca_report_result.get('root_cause'),
            severity=rca_report_result.get('severity'),
            confidence_score=rca_report_result.get('confidence_score'),
            recommendation=rca_report_result.get('recommendation'),
            retry_steps=rca_report_result.get('retry_steps'),
            log_id=failed_log.id,
            github_analysis_id=db_gh_analysis.id
        )

        flash("AI Root Cause Analysis completed successfully!", "success")
        return redirect(url_for('report.view_report', report_id=report.id))

    except Exception as e:
        current_app.logger.error(f"Error during AI analysis pipeline: {str(e)}", exc_info=True)
        flash(f"An error occurred during AI analysis: {str(e)}", "danger")
        return redirect(url_for('dashboard'))
        
@analysis_bp.route('/github-analysis', methods=['GET'])
def github_analysis_view():
    """
    Explore fetched commits and repository code changes directly.
    """
    gh_service = GitHubService(
        token=current_app.config['GITHUB_TOKEN'],
        repo=current_app.config['GITHUB_REPO']
    )
    commits = gh_service.fetch_recent_commits(limit=5)
    is_live = gh_service.is_configured()
    
    return render_template(
        'github_analysis.html', 
        commits=commits, 
        repo=current_app.config['GITHUB_REPO'] or "Not Configured (Showing Simulation Diffs)",
        is_live=is_live
    )
