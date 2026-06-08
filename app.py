import os
import logging
# pyrefly: ignore [missing-import]
from flask import Flask, render_template
from config import Config
from models import init_db
from services.db_service import DBService

# Configure Logging
LOG_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
for log_file in ['app.log', 'error.log', 'success.log']:
    open(os.path.join(LOG_DIR, log_file), 'a', encoding='utf-8').close()

class SuccessOnlyFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage().lower()
        return 'success' in message or 'successful' in message

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

app_handler = logging.FileHandler(os.path.join(LOG_DIR, 'app.log'), encoding='utf-8')
app_handler.setFormatter(formatter)

error_handler = logging.FileHandler(os.path.join(LOG_DIR, 'error.log'), encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

success_handler = logging.FileHandler(os.path.join(LOG_DIR, 'success.log'), encoding='utf-8')
success_handler.setLevel(logging.INFO)
success_handler.addFilter(SuccessOnlyFilter())
success_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(stream_handler)
root_logger.addHandler(app_handler)
root_logger.addHandler(error_handler)
root_logger.addHandler(success_handler)

logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize config folders programmatically
    config_class.init_app(app)

    # Initialize MongoDB (with automatic mock fallback in case server is down)
    init_db(app.config['MONGODB_URI'])

    # Register Blueprints
    from routes.upload_routes import upload_bp
    from routes.analysis_routes import analysis_bp
    from routes.report_routes import report_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(report_bp)

    # Dashboard / Home route
    @app.route('/')
    def dashboard():
        try:
            stats = DBService.get_dashboard_stats()
        except Exception as e:
            logger.error(f"Failed to get dashboard statistics: {str(e)}")
            stats = {
                "total_reports": 0,
                "total_logs": 0,
                "severity_counts": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
                "avg_confidence": "N/A",
                "recent_reports": []
            }
        return render_template('dashboard.html', stats=stats)

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html', error_title="404 Page Not Found", error_message="The page you requested could not be located."), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('base.html', error_title="500 Internal Server Error", error_message="An unexpected server error occurred. Please check application logs."), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
