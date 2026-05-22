import logging
from typing import Optional

# Global flag to ensure basicConfig is called only once
_logging_configured = False


def get_logger(app_name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    @param app_name: Name of the application/module
    @param level: Logging level (defaults to INFO)
    @return: Configured logger instance
    """
    global _logging_configured
    
    # Configure logging only once
    if not _logging_configured:
        logging.basicConfig(
            format='%(asctime)s,%(msecs)d %(levelname)-3s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=level or logging.INFO
        )
        _logging_configured = True
    
    logger = logging.getLogger(app_name)
    if level:
        logger.setLevel(level)
    
    return logger
