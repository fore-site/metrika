import json
import logging
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        # Safely include correlation_id if present (filter may not always run)
        correlation_id = getattr(record, 'correlation_id', None)
        if correlation_id:
            log_obj['correlation_id'] = correlation_id
        if record.exc_info and record.exc_info[1]:
            log_obj['exception'] = str(record.exc_info[1])

        return json.dumps(log_obj)