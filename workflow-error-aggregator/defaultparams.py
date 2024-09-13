from typing_extensions import Protocol

# Configurations
class WorkflowErrorAggregatorParameters:
    """
    User configuration for the workflow error aggregator program. Default parameters can be set here.
    """

    PIPELINE_ID: str = ""
    BASE_URL: str = ""  # e.g. https://api.tetrascience-uat.com/v1/
    USER_TOKEN: str = ""
    ENV_URL: str = ""
    ORG_SLUG: str = ""
    ENV: str = ""

    LIMIT: int = 100  # how many workflows you want to fetch, time descending order
    FILTER: str = "failed"  # lower case
    SIMILARITY_RATIO: float = 0.5  # if you want to 100% match, set it to 1
    START_DATETIME: str = ""  # Formats: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD
    END_DATETIME: str = ""
    VERIFY_SSL: bool = True  # Some customer environments use self-signed certificates
    # which fail ssl verification

    USE_LATEST_PROTOCOL: bool = False  # If true, results are filtered based on the version number of the current protocol number of for the version pipeline.
    PROTOCOL_VERSION: str = "v1.0.0"
    USE_LATEST_PIPELINE: bool = False  # If true, results are filtered based on the timestamp of the last pipeline update or START_DATETIME, whichever is later.
    PLATFORM_VERSION: str = "v3.6.1"  # Must have format of "vX.Y.Z", e.g. "v3.3.4"
    LOG_ROOT = "/tmp/"
    SAVE_DIR = "."
    HTML_OUTPUT_NAME = ENV + "_" + PIPELINE_ID + "_out"
    CSV_OUTPUT_NAME: str = ""
    RAW_FILE_NAME = "raw_file_ids"
    TRUNCATE_RAW_FILE_IDS = 10

    def __init__(self):
        self.make_env_url()

    def make_env_url(self):
        if self.ENV_URL:
            return
        else:
            self.ENV_URL = self.BASE_URL.replace("//api.", "//").replace("/v1/", "/")


class GetSourceFilesParameters(Protocol):
    PIPELINE_ID: str
    BASE_URL: str
    ENV_URL: str
    TS_AUTH_TOKEN: str
    X_ORG_SLUG: str
    LIMIT: int
    FILTER: str
    SIMILARITY_RATIO: float
    START_DATETIME: str
    END_DATETIME: str
    VERIFY_SSL: bool
    USE_LATEST_PROTOCOL: bool
    PROTOCOL_VERSION: str
    USE_LATEST_PIPELINE: bool
    PLATFORM_VERSION: str
    LOG_ROOT: str
    SAVE_DIR: str
    HTML_OUTPUT_NAME: str
    CSV_OUTPUT_NAME: str
    CREATE_RAW_FILE_ID_OUTPUT: bool
    RAW_FILE_NAME: str
