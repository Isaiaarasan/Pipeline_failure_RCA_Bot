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

        # Check if the file is in the request
        file_key = 'log_file'
        if file_key not in request.files:
            flash("No file part in the request.", "danger")
            return redirect(url_for('upload.upload_log'))

        file = request.files[file_key]
        if file.filename == '':
            flash("No file selected.", "danger")
            return redirect(url_for('upload.upload_log'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Read content
            try:
                content = file.read().decode('utf-8', errors='ignore')
                
                # Save physically to the uploads directory
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.seek(0)
                file.save(upload_path)
                
                # Save to Database using DB Service
                log_record = DBService.save_log(
                    filename=filename,
                    log_type=log_type,
                    content=content
                )
                
                flash(f"Successfully uploaded {log_type} log: {filename}", "success")
                
                if log_type == 'failure':
                    # Guide user to start the analysis directly
                    return redirect(url_for('analysis.analyze', log_id=log_record.id))
                else:
                    return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f"Error processing log file: {str(e)}", "danger")
                return redirect(url_for('upload.upload_log'))
        else:
            flash("Invalid file extension. Please upload a .txt or .log file.", "danger")
            return redirect(url_for('upload.upload_log'))

    return render_template('upload.html')
