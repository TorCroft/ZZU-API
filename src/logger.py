from datetime import datetime, timezone, timedelta
import logging, sys, os, glob, re

LOG_FOLDER = "logs"
MAX_LOG_FILES = 14

if not os.path.exists(LOG_FOLDER):
    os.mkdir(LOG_FOLDER)

# Define a UTC+8 timezone offset
UTC_OFFSET = timezone(timedelta(hours=8))

# New log file name
LOG_FILE = f"log_{datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(UTC_OFFSET).strftime('%Y%m%d')}.log"

def cleanup_logs(log_folder, max_log_files=30):
    # Get a list of log files in the specified folder
    log_files = glob.glob(os.path.join(log_folder, "log_*.log"))

    # Sort log files based on timestamp in the filenames (in descending order)
    log_files.sort(key=lambda x: int(re.search(r"log_(\d{8}).log", x).group(1)), reverse=True)

    # Check if the number of log files exceeds the maximum limit
    if len(log_files) > max_log_files:
        # Calculate the number of files to delete
        files_to_delete = len(log_files) - max_log_files

        # Delete the older log files beyond the maximum limit
        for _ in range(files_to_delete):
            file_to_delete = log_files.pop()  # Get the oldest log file
            os.remove(file_to_delete)
            logger.debug(f"Deleted log file: {file_to_delete}")

# Create a custom formatter that includes UTC+8 time and line number in the log messages
class Formatter(logging.Formatter):
    def __init__(self):
        super(Formatter, self).__init__(datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record):
        record.asctime = self.formatTime(record)
        log_line = f'[{record.asctime} UTC+8] [{record.levelname}] [{record.filename} line {record.lineno}] {record.msg}'
        return log_line

    def formatTime(self, record):
        return datetime.fromtimestamp(record.created, tz=timezone.utc).astimezone(UTC_OFFSET).strftime(self.datefmt)

# Create a formatter using the custom Formatter class with the desired date format
formatter = Formatter()

# Create a logger instance
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # Set the desired logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Create a file handler to log to a file
file_handler = logging.FileHandler(os.path.join(LOG_FOLDER, LOG_FILE), encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create a console handler to log to the console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # Set the desired logging level for the console
console_handler.setFormatter(formatter)

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

cleanup_logs(LOG_FOLDER, MAX_LOG_FILES)
