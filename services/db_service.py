from datetime import datetime
import logging
import models

logger = logging.getLogger(__name__)

def get_db():
    """Get database instance, raising error if not initialized."""
    db = models.db
    if db is None:
        logger.error("Database not initialized")
        raise RuntimeError("Database connection not established")
    return db

def get_next_sequence_value(sequence_name):
    """
    Generates a sequential auto-incrementing integer ID using a counters collection.
    """
    db = models.db
    if db is None:
        logger.error("Database not initialized")
        raise RuntimeError("Database connection not established")
    
    from pymongo import ReturnDocument
    counter = db.counters.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return counter['sequence_value']

class MongoDoc:
    """
    A lightweight wrapper around a MongoDB dictionary that exposes keys as attributes
    and dynamically resolves virtual relationships (log, github_analysis).
    This keeps Flask templates and routes completely compatible.
    """
    def __init__(self, data):
        self.__dict__['_data'] = data

    def __getattr__(self, name):
        if name == 'id':
            return self._data.get('_id')
        if name == 'log':
            log_id = self._data.get('log_id')
            if log_id:
                try:
                    db = get_db()
                    log_doc = db.logs.find_one({'_id': log_id})
                    return MongoDoc(log_doc) if log_doc else None
                except RuntimeError:
                    return None
            return None
        if name == 'github_analysis':
            ga_id = self._data.get('github_analysis_id')
            if ga_id:
                try:
                    db = get_db()
                    ga_doc = db.github_analysis.find_one({'_id': ga_id})
                    return MongoDoc(ga_doc) if ga_doc else None
                except RuntimeError:
                    return None
            return None
        return self._data.get(name)

    def __setattr__(self, name, value):
        if name == 'id':
            self._data['_id'] = value
        else:
            self._data[name] = value

    def to_dict(self):
        d = self._data.copy()
        d['id'] = d.get('_id')
        return d

class DBService:
    @staticmethod
    def save_log(filename, log_type, content):
        """
        Saves a pipeline log to the logs collection.
        """
        try:
            db = get_db()
            log_id = get_next_sequence_value('logs')
            log_doc = {
                '_id': log_id,
                'filename': filename,
                'log_type': log_type,
                'content': content,
                'uploaded_at': datetime.utcnow()
            }
            db.logs.insert_one(log_doc)
            return MongoDoc(log_doc)
        except Exception as e:
            logger.error(f"Error saving log to MongoDB: {e}")
            raise e

    @staticmethod
    def get_latest_success_log():
        """
        Retrieves the most recently uploaded successful pipeline log.
        """
        try:
            db = get_db()
            results = db.logs.find(
                {'log_type': 'success'},
                sort=[('uploaded_at', -1)]
            )
            # Convert first result if exists
            results_list = list(results)
            return MongoDoc(results_list[0]) if results_list else None
        except RuntimeError:
            return None

    @staticmethod
    def save_github_analysis(commit_id, changed_files, diff_summary):
        """
        Saves GitHub analysis results to the database.
        """
        try:
            db = get_db()
            db = get_db()
            ga_id = get_next_sequence_value('github_analysis')
            ga_doc = {
                '_id': ga_id,
                'commit_id': commit_id,
                'changed_files': changed_files or [],
                'diff_summary': diff_summary,
                'analyzed_at': datetime.utcnow()
            }
            db.github_analysis.insert_one(ga_doc)
            return MongoDoc(ga_doc)
        except Exception as e:
            logger.error(f"Error saving github analysis to MongoDB: {e}")
            raise e

    @staticmethod
    def save_report(failure_summary, root_cause, severity, confidence_score, recommendation, retry_steps, log_id=None, github_analysis_id=None):
        """
        Saves an RCA report to the database.
        """
        try:
            db = get_db()
            report_id = get_next_sequence_value('reports')
            report_doc = {
                '_id': report_id,
                'failure_summary': failure_summary,
                'root_cause': root_cause,
                'severity': severity,
                'confidence_score': confidence_score,
                'recommendation': recommendation,
                'retry_steps': retry_steps,
                'created_at': datetime.utcnow(),
                'log_id': log_id,
                'github_analysis_id': github_analysis_id
            }
            db.reports.insert_one(report_doc)
            return MongoDoc(report_doc)
        except Exception as e:
            logger.error(f"Error saving report to MongoDB: {e}")
            raise e

    @staticmethod
    def get_report_by_id(report_id):
        """
        Retrieves a report by its primary key ID.
        """
        try:
            db = get_db()
            report_data = db.reports.find_one({'_id': report_id})
            return MongoDoc(report_data) if report_data else None
        except RuntimeError:
            return None

    @staticmethod
    def get_all_reports():
        """
        Retrieves all generated reports, ordered newest first.
        """
        try:
            db = get_db()
            reports = db.reports.find(
                sort=[('created_at', -1)]
            )
            return [MongoDoc(r) for r in reports]
        except RuntimeError:
            return []

    @staticmethod
    def get_dashboard_stats():
        """
        Gathers key statistics for the dashboard UI.
        """
        try:
            db = get_db()
            total_reports = db.reports.count_documents({})
            total_logs = db.logs.count_documents({})
            
            # Severity breakdown
            reports = db.reports.find()
            severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            total_conf = 0
            conf_count = 0
            
            for r in reports:
                sev = r.get('severity', 'Medium').capitalize()
                if sev in severity_counts:
                    severity_counts[sev] += 1
                else:
                    severity_counts["Medium"] += 1
                    
                conf_str = r.get('confidence_score')
                if conf_str:
                    clean_conf = conf_str.replace('%', '').strip()
                    try:
                        total_conf += float(clean_conf)
                        conf_count += 1
                    except ValueError:
                        val_map = {"high": 85.0, "medium": 65.0, "low": 45.0}
                        mapped_val = val_map.get(clean_conf.lower())
                        if mapped_val:
                            total_conf += mapped_val
                            conf_count += 1

            avg_confidence = f"{round(total_conf / conf_count, 1)}%" if conf_count > 0 else "N/A"
            
            # Get recent 5 reports. Support both PyMongo cursor (with .limit) and mock list returns.
            recent_cursor = db.reports.find(sort=[('created_at', -1)])
            try:
                if hasattr(recent_cursor, 'limit'):
                    recent_iter = recent_cursor.limit(5)
                    recent_reports = [MongoDoc(r) for r in recent_iter]
                else:
                    recent_list = list(recent_cursor)
                    recent_reports = [MongoDoc(r) for r in recent_list[:5]]
            except Exception:
                recent_list = list(recent_cursor)
                recent_reports = [MongoDoc(r) for r in recent_list[:5]]

            return {
                "total_reports": total_reports,
                "total_logs": total_logs,
                "severity_counts": severity_counts,
                "avg_confidence": avg_confidence,
                "recent_reports": recent_reports
            }
        except RuntimeError:
            return {
                "total_reports": 0,
                "total_logs": 0,
                "severity_counts": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
                "avg_confidence": "N/A",
                "recent_reports": []
            }
