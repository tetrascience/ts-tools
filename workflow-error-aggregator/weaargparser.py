import argparse
from defaultparams import GetSourceFilesParameters
from loguru import logger
import re


class WeaArgParser:
    def __init__(self) -> GetSourceFilesParameters:
        # get command line arguments
        self.parser = None
        self.initiate_parser()

    def __assure_positive_int(self, val, allow_neg_one=False):
        try:
            float_val = float(val)
            if float_val.is_integer() and allow_neg_one and int(float_val) == -1:
                return -1
            if not float_val.is_integer() or float_val < 1:
                msg = f"{val} is not a positive integer."
                logger.error(msg)
                raise argparse.ArgumentTypeError(msg)
        except ValueError as err:
            msg = f"{val} is not numeric. Please specify a positive integer."
            logger.error(msg)
            raise argparse.ArgumentTypeError(msg)
        return int(float_val)

    def __assure_positive_int_neg_one(self, val):
        """
        wrapper function to set allow_neg_one to true
        """
        return self.__assure_positive_int(val, allow_neg_one=True)

    def __assure_between_zero_one(self, val):
        try:
            float_val = float(val)
            if float_val > 1.0 or float_val < 0.0:
                msg = f"{val} is not between 0 and 1, inclusive."
                logger.error(msg)
                raise argparse.ArgumentTypeError(msg)
        except ValueError as err:
            msg = f"{val} is not numeric. Please specify a float between 0 and 1."
            logger.error(msg)
            raise argparse.ArgumentTypeError(msg)
        return float_val

    def __make_lowercase_str(self, val):
        return val.lower()

    def __check_version_number(self, val):
        """
        Checks to make sure a user-defined version number matches the format vX.Y.Z. Also allows Z to be an asterisk, e.g. v3.2.*, or the final number to be left off, e.g. v3.2, since the API depends only on major and minor numbers.
        """
        if val.lower() == "none":
            return None
        regex = "^(v|V)?(\d+\.)((\d+\.\*)|\d+(\.\d+)?)$"
        pattern = re.compile(regex)
        if bool(pattern.match(val)):
            if val[0] not in ["v", "V"]:
                val = "v" + val
                logger.info(
                    f"Prefixing version number with a 'v'. Version number is now {val}."
                )
            return val.lower()
        else:
            msg = f"{val} is not a valid version number. Please specify a version number in the format 'vX.Y.Z', e.g. 'v3.1.7'."
            logger.error(msg)
            raise argparse.ArgumentTypeError(msg)

    def initiate_parser(self):
        self.parser = argparse.ArgumentParser(
            prog="workflow_error-aggregator",
            description="""
            The workflow error aggregator (WEA) script will search for workflows of a given pipeline ID and aggregate all the errors, so you can easily tell how many unique error there are and the count of each error type.
            """,
        )

    def parse_input_args(self):
        return self.parser.parse_args()

    def parser_setup(self, default: GetSourceFilesParameters) -> None:

        self.parser.add_argument(
            "-p",
            "--pipeline-id",
            dest="pipeline_id",
            default=default.PIPELINE_ID,
            help="UUID of the pipeline to be used.",
        )

        self.parser.add_argument(
            "-u",
            "--url",
            dest="url",
            metavar="BASE_URL",
            default=default.BASE_URL,
            help=f"Set the API url. Default is set in defaultparams.py to {default.BASE_URL}.",
        )

        self.parser.add_argument(
            "-E",
            "--env-url",
            dest="env_url",
            metavar="ENV_URL",
            default=default.ENV_URL,
            help=f"Set the environment/TDP url. Default is set in defaultparams.py to {default.ENV_URL}. Optional; used for aggregated output file links.",
        )

        self.parser.add_argument(
            "-t",
            "--token",
            dest="user_token",
            default=default.USER_TOKEN,
            help="Set the user token. May also be set in defaultparams.py.",
        )

        self.parser.add_argument(
            "-o",
            "--org-slug",
            dest="org_slug",
            default=default.ORG_SLUG,
            help=f"Set the org-slug. Default is set in main.py to {default.ORG_SLUG}.",
        )

        self.parser.add_argument(
            "-l",
            "--limit",
            dest="limit",
            type=self.__assure_positive_int,
            default=default.LIMIT,
            help="Maximum number of workflows to attempt to find.",
        )

        self.parser.add_argument(
            "-f",
            "--filter",
            dest="filter",
            type=self.__make_lowercase_str,
            default=default.FILTER,
            help="String description of workflow type. For failed files, this should be set to failed; however, this could also be set to pending or completed for those respective files.",
        )

        self.parser.add_argument(
            "-z",
            "--sim-ratio",
            dest="similarity_ratio",
            type=self.__assure_between_zero_one,
            default=default.SIMILARITY_RATIO,
            help="Number between 0 and 1 (inclusive) for how similar error messages can be and still be grouped together. Setting to 1 means errors must be identical to be grouped together.",
        )

        self.parser.add_argument(
            "-b",
            "--begin",
            dest="start_datetime",
            type=str,
            default=default.START_DATETIME,
            help="Earliest date/time for the file search.",
        )

        self.parser.add_argument(
            "-e",
            "--end",
            dest="end_datetime",
            type=str,
            default=default.END_DATETIME,
            help="Latest date/time for the file search.",
        )

        self.parser.add_argument(
            "-S",
            "--ssl",
            dest="verify_ssl",
            default=default.VERIFY_SSL,
            help="If flag is present, then ssl verification is used when fetching files.",
        )

        self.parser.add_argument(
            "-q",
            "--latest-protocol",
            action="store_true",
            dest="use_latest_protocol",
            default=default.USE_LATEST_PROTOCOL,
            help="If true, results are filtered based on the version number of the current protocol number of for the version pipeline. This behavior only works for TDP v3.2.* and later. For TDP v3.1.*, `PROTOCOL_VERSION` must be specified. If `USE_LATEST_PROTOCOL` is `True` and `PROTOCOL_VERSION` is specified for TDP v3.2.* and later, the `USE_LATEST_PROTOCOL` flag takes precedence.",
        )

        self.parser.add_argument(
            "-Q",
            "--protocol-version",
            type=self.__check_version_number,
            dest="protocol_version",
            default=default.PROTOCOL_VERSION,
            help="Specified protocol version to match for errors. If `USE_LATEST_PROTOCOL` is `True` and `PROTOCOL_VERSION` is specified for TDP v3.2.* and later, the `USE_LATEST_PROTOCOL` flag takes precedence.",
        )

        self.parser.add_argument(
            "-P",
            "--latest-pipeline",
            action="store_true",
            dest="use_latest_pipeline",
            default=default.USE_LATEST_PIPELINE,
            help="If true, results are filtered based on the timestamp of the last pipeline configuration update or START_DATETIME, whichever is later. Note that this automatically ensures the use of the latest protocol.",
        )

        self.parser.add_argument(
            "-v",
            "--version",
            dest="platform_version",
            type=self.__check_version_number,
            default=default.PLATFORM_VERSION,
            help="Version of the TDP platform. Must have format of 'vX.Y.Z', e.g. 'v3.3.4'.",
        )

        self.parser.add_argument(
            "-s",
            "--save-dir",
            dest="save_dir",
            default=default.SAVE_DIR,
            help="Path to the save_dir. Default is the current directory.",
        )

        self.parser.add_argument(
            "-r",
            "--raw-output",
            type=str,
            dest="raw_file_name",
            default=default.RAW_FILE_NAME,
            help=f"File name of the list of the raw file ids. Should not contain the extension or path. If set to 'None' or '' (empty string), then no file is generated. Default: {default.RAW_FILE_NAME}",
        )

        self.parser.add_argument(
            "-H",
            "--html-output",
            type=str,
            dest="html_output_name",
            default=default.HTML_OUTPUT_NAME,
            help=f"File name of html output file of the aggregated workflow errors. Should not contain the extension or path. If set to 'None' or '' (empty string), then no file is generated. Default: {default.HTML_OUTPUT_NAME}",
        )

        self.parser.add_argument(
            "-C",
            "--csv-output",
            type=str,
            dest="csv_output_name",
            default=default.CSV_OUTPUT_NAME,
            help=f"File name of csv output file of the aggregated workflow errors. Should not contain the extension or path. If set to 'None' or '' (empty string), then no file is generated. Default: {default.CSV_OUTPUT_NAME}",
        )

        self.parser.add_argument(
            "-L",
            "--log-root",
            dest="log_root",
            default=default.LOG_ROOT,
            help="Sets the base directory for log files from the program.",
        )

        self.parser.add_argument(
            "-T",
            "--truncate",
            dest="truncate_raw_file_ids",
            type=self.__assure_positive_int_neg_one,
            default=default.TRUNCATE_RAW_FILE_IDS,
            help="Limit the number of file IDs in the file ID output file to this value.",
        )
