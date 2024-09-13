import pandas as pd
from difflib import SequenceMatcher
from pydash import get as _get
from loguru import logger

# Defaults
DEFAULT_SIMILARITY_RATIO = 1
ANALYSIS_FIELDS = ["id", "createdAt", "lastUpdatedAt", "tasks"]

# For truncating error messages to speed up the error comparison process. Comparing strings with SequenceMatcher is linear w.r.t. string length on average case but quadratic on worst case. This behavior may be too slow with full messages with large numbers of messages and message groups
ERROR_MESSAGE_TRUNCATION_LENGTH = 300

# Ordering:
#   grab task-script "output" logs
#   if no output, grab "logs" because when windows task-scripts fail, output is stored in "logs"
#   if no output and no logs, grab master-script level logs

DEFAULT_EXTRACT_FIELDS = {
    "task_output": "tasks.-1.output",
    "task_log": "tasks.-1.log",
    "masterScriptLogs": "masterScriptLogs",
    "file_id": "inputFile.fileId",
}

TASK_EVAL_FIELDS = ["tasks", "supersededTasks"]


def eval_task_log(tasks: list) -> list:
    return [
        {
            k: [eval(x) for x in v.split("\n")] if k == "log" else v
            for k, v in task.items()
        }
        for task in tasks
    ]


def workflow_result_to_dataframe(workflows: list, **extract_fields: str) -> pd.DataFrame:
    """
    Convert the list of workflow results to a dataframe and subset on fields of interest.

    By default this converts the result to a dataframe and extracts the following fields
    from each record: "tasks", "masterScriptLogs", "id", "createdAt", "lastUpdatedAt".
    It will further process the result by unnesting the fields "output" and "log" from the
    last element of "tasks".

    You may add to the returned columns by setting keyword arguments with output column to
    extracted field (using pydash.get() syntax).
    Example:

    >>> workflow_result_to_dataframe(workflows, md_department="inputFile.customMetadata.Department")

    """

    all_extract_fields = {**DEFAULT_EXTRACT_FIELDS, **extract_fields}

    workflow_dataframe = pd.DataFrame.from_dict(workflows)

    # Do some string to dict conversions on some fields for better access
    for field in TASK_EVAL_FIELDS:
        if field in workflow_dataframe:
            workflow_dataframe[field] = workflow_dataframe[field].apply(eval_task_log)

    for field, location in all_extract_fields.items():
        workflow_dataframe[field] = workflow_dataframe.apply(
            lambda x: _get(x, location), axis=1
        )

    return workflow_dataframe[ANALYSIS_FIELDS + list(all_extract_fields.keys())]


def aggregate_workflow_errors(
    workflows: pd.DataFrame,
    similarity_ratio: float = DEFAULT_SIMILARITY_RATIO,
    fields: list = list(DEFAULT_EXTRACT_FIELDS.keys()),
    status: str = "failed",
) -> dict:
    errors = []
    no_error_found_workflow_count = 0
    file_id_list = []

    logger.info(f"Aggregating workflows.")

    status_statement = "error" if status.lower() == "failed" else "message"

    workflow_count = 0

    for workflow in workflows.to_dict(orient="records"):
        workflow_count += 1
        if workflow_count % 100 == 0:
            logger.info(
                f"Aggregating workflow {workflow_count} of {len(workflows.index)}"
            )

        if len(workflow["tasks"]) == 0:
            logger.info(
                f"No tasks found with workflow ID {workflow['id']}, skipping..."
            )
            continue

        error = None
        for field in fields:
            error = workflow[field]
            if error:
                break
        else:
            logger.info(
                f"No {status_statement} found for workflow id: {workflow['id']}, skipping..."
            )
            no_error_found_workflow_count += 1
            continue

        workflow_summary = (
            workflow["id"],
            workflow["createdAt"][:-5],
            workflow["lastUpdatedAt"][:-5],
            workflow["file_id"],
        )

        found_similar_error = False

        file_id_list.append(workflow["file_id"])

        curr_error_msg = str(_get(error, "result.message"))
        if not curr_error_msg:
            curr_error_msg = str(error)

        for existing_err in errors:
            exist_err_msg = str(_get(existing_err, "value.result.message"))
            if not exist_err_msg:
                exist_err_msg = str(_get(existing_err, "value"))
            if not exist_err_msg:
                exist_err_msg = str(existing_err)

            a = len(curr_error_msg)
            b = curr_error_msg[:ERROR_MESSAGE_TRUNCATION_LENGTH]

            if (
                similarity_ratio == DEFAULT_SIMILARITY_RATIO
                and curr_error_msg == exist_err_msg
            ):
                found_similar_error = True
            elif curr_error_msg == exist_err_msg:
                found_similar_error = True
            elif (
                # Note the truncation of message length; this is useful since comparing strings with SequenceMatcher is linear on average case but quadratic on worst case. For large numbers of error messages, this may be problematic.
                similarity_ratio != DEFAULT_SIMILARITY_RATIO
                and SequenceMatcher(
                    None,
                    curr_error_msg[:ERROR_MESSAGE_TRUNCATION_LENGTH],
                    exist_err_msg[:ERROR_MESSAGE_TRUNCATION_LENGTH],
                ).ratio()
                >= similarity_ratio
            ):
                found_similar_error = True

            if found_similar_error:
                existing_err["count"] += 1
                existing_err["workflow_info"].append(workflow_summary)
                break

        if not found_similar_error:
            errors.append(
                {
                    "value": error,
                    "count": 1,
                    "workflow_info": [workflow_summary],
                }
            )
            logger.debug(
                f"No same {status_statement} found. Added {error} to {status_statement} list as a new {status_statement}"
            )

    logger.info(
        f"There are {no_error_found_workflow_count} {status} workflows with no {status_statement} found"
    )
    return errors, file_id_list
