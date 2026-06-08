import os
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from services.db_service import DBService

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'txt', 'log'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload-log', methods=['GET', 'POST'])
def upload_log():
    if request.method == 'POST':
        log_type = request.form.get('log_type')
        if log_type not in ['failure', 'success']:
            flash("Invalid log type specified.", "danger")
            return redirect(url_for('upload.upload_log'))

        file = request.files.get('log_file')

        if not file or file.filename == '':
            flash("Please select a log file to upload.", "danger")
            return redirect(url_for('upload.upload_log'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            content = file.read().decode('utf-8', errors='ignore')
        else:
            flash("Invalid file extension. Please upload a .txt or .log file.", "danger")
            return redirect(url_for('upload.upload_log'))

        # Save physically to the uploads directory
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        with open(upload_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Save to Database using DB Service
        log_record = DBService.save_log(
            filename=filename,
            log_type=log_type,
            content=content
        )

        flash(f"Successfully uploaded {log_type} log: {filename}", "success")

        if log_type == 'failure':
            return redirect(url_for('analysis.analyze', log_id=log_record.id))
        else:
            return redirect(url_for('dashboard'))

    return render_template('upload.html')
