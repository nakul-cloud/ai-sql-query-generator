"""
logger.py

Production-grade logging configuration
for AI SQL Query Generator systems.

Responsibilities
----------------
- Centralized log formatting
- Log level management
- Output routing (console, file)

Author
------
AI SQL Query Generator Project
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler


def configure_logger():
    """
    Configures the root logger with standard formatting.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Optional: Add file handler if needed in future
    # log_dir = "logs"
    # os.makedirs(log_dir, exist_ok=True)
    # file_handler = RotatingFileHandler(
    #     os.path.join(log_dir, "app.log"), maxBytes=5*1024*1024, backupCount=2
    # )
    # file_handler.setFormatter(logging.Formatter(log_format))
    # logging.getLogger().addHandler(file_handler)

# Execute configuration immediately on import
configure_logger()
