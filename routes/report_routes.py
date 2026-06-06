from flask import Blueprint, render_template, abort, send_file, flash, redirect, url_for
from services.db_service import DBService
from services.pdf_service import PDFService

report_bp = Blueprint('report', __name__)

@report_bp.route('/history', methods=['GET'])
def history():
    """
    Renders list of previous RCA reports.
    """
    reports = DBService.get_all_reports()
    return render_template('history.html', reports=reports)

@report_bp.route('/report/<int:report_id>', methods=['GET'])
def view_report(report_id):
    """
    Renders the detailed view of a specific RCA report.
    """
    report = DBService.get_report_by_id(report_id)
    if not report:
        abort(404, description="RCA Report not found.")
        
    return render_template('report.html', report=report)

@report_bp.route('/export-pdf/<int:report_id>', methods=['GET'])
def export_pdf(report_id):
    """
    Generates and downloads a PDF of the selected RCA report.
    """
    report = DBService.get_report_by_id(report_id)
    if not report:
        abort(404, description="RCA Report not found.")
        
    try:
        pdf_buffer = PDFService.generate_rca_pdf(report)
        filename = f"RCA_Report_{report_id:04d}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f"Failed to generate PDF: {str(e)}", "danger")
        return redirect(url_for('report.view_report', report_id=report_id))
