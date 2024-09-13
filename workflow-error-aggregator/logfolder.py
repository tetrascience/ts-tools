from datetime import datetime
import pathlib
from loguru import logger
from typing import Union
import sys


def configure_logging(
    root: Union[str, pathlib.Path] = "/tmp/",
    friendly_name: str = "workflow-error-aggregator",
) -> None:
    """
    Configures the loguru logger to also save a file in the root directory provided.
    """
    # set stdout debugger to not have debug info, which will only be put into the log file.
    logger.configure(handlers=[{"sink": sys.stdout, "level": "INFO"}])
    LogFolder.set_path(root, friendly_name)
    logger_path = LogFolder.folder.joinpath(
        f"{str(datetime.now()).replace(':', '-').replace(' ', '_')}.log"
    )
    logger.info(f"Logging information will be saved to {logger_path}")
    logger.add(logger_path)


class LogFolder:
    """
    Creates a log folder in a provided root directory.
    copied from
    https://github.com/TinyTheBrontosaurus/nhl-ai/blob/0209388919ef8795c8f3eff14675b3b4df3adb31/crosscheck/log_folder.py#L7-L24
    """

    folder = pathlib.Path.cwd()
    friendly_name = None
    start_time = datetime.now()
    latest_log_folder: pathlib.Path = None
    latest_log_folder_checked = False

    @classmethod
    def set_path(cls, root: pathlib.Path, friendly_name: str):
        # Setup target log folder
        the_date = cls.start_time.date()
        cls.friendly_name = friendly_name
        cls.folder = pathlib.Path(root) / cls.friendly_name / str(the_date)

        # Create the folders
        cls.folder.mkdir(parents=True, exist_ok=True)


def log_parameters(params):
    """
    Logs the program's parameters for the log file.
    """
    for k, v in params.__dict__.items():
        if k == "user_token":
            continue  # skip user_token for security
        logger.debug(f"{k}: {v}")
