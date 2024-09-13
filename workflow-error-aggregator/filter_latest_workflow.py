from dateutil import parser
from pydash import get as _get
from defaultparams import GetSourceFilesParameters
from loguru import logger


def filter_latest_workflow(
    workflows: list, pipeline_parameters: GetSourceFilesParameters
) -> list:
    """Filter workflows with the same S3 input file key and only keep the latest workflows.
    This is because the same file may be processed multiple times.
    Most times we are only interested in the latest workflow result.

    Args:
        workflows (list): all the workflows

    Returns:
        list: filtered workflows
    """

    logger.info(f"Filtering workflows.")
    # strictly for logging messages
    filter_str = f"{pipeline_parameters.filter} " if pipeline_parameters.filter else ""

    # first check whether version of workflow matches the current version of the protocol, if use_latest_protocol is True or PROTOCOL_VERSION is specified.
    if ("v3.1" not in pipeline_parameters.platform_version) or (
        "v3.1" in pipeline_parameters.platform_version
        and pipeline_parameters.protocol_version
    ):
        protocol_workflows = []
        for workflow in workflows:
            if (
                _get(workflow, "protocolVersion")
                == pipeline_parameters.protocol_version
            ):
                protocol_workflows.append(workflow)
        workflows = protocol_workflows

        if len(protocol_workflows) == 0:
            logger.warning(
                f"No {filter_str}workflows found with protocol version {pipeline_parameters.protocol_version}. No output will be generated."
            )
            return workflows
        else:
            logger.info(
                f"{len(workflows)} {filter_str}workflows found with protocol version {pipeline_parameters.protocol_version}."
            )

    input_file_with_latest_workflow = {}  # { "input_file_key": <workflow dict> }
    duplicates = 0
    for workflow in workflows:

        input_file_key = _get(workflow, "inputFile.fileKey")

        # found the same file path
        if input_file_key in input_file_with_latest_workflow.keys():
            # duplicate found
            duplicates += 1
            existing_wf = input_file_with_latest_workflow[input_file_key]
            existing_wf_last_updated_at = parser.parse(
                _get(existing_wf, "lastUpdatedAt")
            )
            current_wf_created_at = parser.parse(_get(workflow, "createdAt"))

            if current_wf_created_at > existing_wf_last_updated_at:
                input_file_with_latest_workflow[input_file_key] = workflow
        # no same file path found
        else:
            input_file_with_latest_workflow[input_file_key] = workflow

    latest_wfs = input_file_with_latest_workflow.values()
    logger.info(
        f"{len(latest_wfs)} {filter_str}workflows using different input files. {duplicates} duplicates found."
    )

    return latest_wfs
