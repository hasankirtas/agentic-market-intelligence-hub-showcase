import logging
import sys

def setup_logger(name: str = "agentic_hub", level: int = logging.INFO):
    """
    Configure compliant logger for the Agentic Market Intelligence Hub.
    
    This is a simplified logging implementation for the showcase repository.
    The production system uses COREUS structured logging with semantic context.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
