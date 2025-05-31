"""
RunLog utility for collecting and managing log messages during test or recording runs.

This class provides a simple interface to accumulate messages, retrieve summaries, and save logs to a file.
"""

from datetime import datetime
from src.utils.config import Config

config = Config()
filepath = config.get_run_log_path()

class RunLog:
    """
    General-purpose log container for test/recording runs.

    Methods
    -------
    add(message, level="INFO")
        Add a message to the log with an optional level.
    get_summary()
        Get the full log as a single string.
    clear()
        Clear all log entries.
    save_to_file(filepath)
        Save the log to a text file.
    """
    def __init__(self):
        self.entries = []

    def add(self, message, level="INFO"):
        """
        Add a message to the log.

        Parameters
        ----------
        message : str
            The message to add.
        level : str, optional
            The log level (e.g., 'INFO', 'WARNING', 'ERROR'). Default is 'INFO'.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.entries.append(f"[{level}] {timestamp}: {message}")

    def get_summary(self):
        """
        Get the full log as a single string.

        Returns
        -------
        str
            The concatenated log entries, separated by newlines.
        """
        return "\n".join(self.entries)

    def clear(self):
        """
        Clear all log entries.
        """
        self.entries.clear()

    def save_to_file(self):
        """
        Save the log to a text file.

        Parameters
        ----------
        filepath : str
            The path to the file where the log should be saved.
        """
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(self.get_summary()) 

    def erase(self):
        """
        Erase the log file.

        Parameters
        ----------
        filepath : str
            The path to the file where the log should be saved.
        """
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("") 