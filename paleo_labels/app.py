"""
Streamlit application (ran locally) for a user to design
at least one paleontological label.
"""

import logging
import time


def main() -> None:
    # initiate logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.get
    # initiate session time tracking
    start_time = time.time()
    print(logger, start_time)
