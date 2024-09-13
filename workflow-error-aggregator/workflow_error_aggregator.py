from requests import get
from loguru import logger
import os
from typing import Tuple
from pydash import get as _get
from time import sleep

from filter_latest_workflow import filter_latest_workflow
from aggregate_workflow_errors import (
    aggregate_workflow_errors,
    workflow_result_to_dataframe,
)
from defaultparams import WorkflowErrorAggregatorParameters, GetSourceFilesParameters
from weaargparser import WeaArgParser
from logfolder import configure_logging, log_parameters
from htmlwriter import make_html_output


API_REQUEST_TIMEOUT = 30  # timeout time for API requests in seconds
MAX_API_RETRY = 3


def get_pipeline_info(params: GetSourceFilesParameters) -> Tuple[list, dict]:
    """Fetches pipeline information based off of the pipeline_id and the limit
     of records to be returned

    Args:
        params (GetSourceFilesParameters): Class wrapper of all user-configurable parameters

    Returns:
        list: List of dicts of pipeline logs
        dict: Dictionary of pipeline configuration parameters
    """

    # Fetch pipeline version/update time information
    logger.info(f"Fetching the pipeline configuration.")
    retry_count = 0
    pipeline_config = None
    while not pipeline_config:
        retry_count += 1
        pipeline_config = get_pipeline_config(params)
        if pipeline_config is None and retry_count >= MAX_API_RETRY:
            logger.error(f"Pipeline configuration could not be retrieved.")
            return [None, None]
        if not pipeline_config:
            logger.warning(
                f"API request for pipeline configuration failed. Retrying (attempt {retry_count})."
            )
            sleep(2.0)

    if params.use_latest_protocol or params.use_latest_pipeline:
        # save version/update time information to param class.
        if "v3.1" not in params.platform_version:
            logger.info("Saving the most recent pipeline information.")
            setattr(
                params,
                "protocol_version",
                _get(pipeline_config, "protocolVersion"),
            )
            setattr(params, "updated_time", _get(pipeline_config, "updatedAt"))
        else:
            logger.warning(
                f"The available APIs for TDP {params.platform_version} do not support the use of `USE_LATEST_PROTOCOL` or `USE_LATEST_PIPELINE`. Please instead specify `PROTOCOL_VERSION` and/or `START_DATETIME`. Continuing..."
            )
            # No pipeline update time present in 3.1 workflow object.
            setattr(params, "updated_time", None)

    # API should use pagination.
    if "v3.1" in params.platform_version:
        api_endpoint = "workflow/workflows"
    else:
        api_endpoint = "workflow/search"

    curr_results_needed = params.limit
    page = 0  # zero-indexed page number
    PAGE_SIZE = 100  # max value allowed by "workflow/search" API
    results_full_list = []
    retry_count = 0
    logger.info(f"Fetching workflows.")
    all_found = False
    while True:
        # do-while loop for retrieving results
        results_per_page = (
            PAGE_SIZE if PAGE_SIZE < curr_results_needed else curr_results_needed
        )
        paged_url = make_url(
            parameters=params,
            api_endpoint=api_endpoint,
            page=page,
            page_size=results_per_page,
        )
        current_list = fetch_results(paged_url, params=params)

        if current_list is None and retry_count >= MAX_API_RETRY:
            logger.warning(
                f"API request failed. Retried {MAX_API_RETRY} time{'s' if MAX_API_RETRY != 1 else ''}."
            )
            if len(results_full_list) > 0:
                logger.warning(
                    f"Proceeding with current list of workflows. Be aware that there may be more {params.filter} workflows not included in this analysis."
                )
            break
        elif current_list is None:
            retry_count += 1
            PAGE_SIZE = max(int(PAGE_SIZE / 2), 5)
            logger.warning(
                f"API request failed. Retrying with {PAGE_SIZE} results per page (attempt {retry_count})."
            )
            sleep(2.0)
            continue
        elif not current_list:
            logger.warning(f"No workflows matching the specified criteria we found.")
            break

        # Merge previous results with new results
        results_full_list = [*results_full_list, *current_list]
        page += 1  # increment page
        curr_results_needed -= PAGE_SIZE  # decrement remaining results needed
        logger.info(f"{len(results_full_list)} total workflows retrieved.")
        if curr_results_needed <= 0 or len(current_list) < PAGE_SIZE:
            all_found = True
            break  # all needed results retrieved

    filter_str = f"{params.filter} " if params.filter else ""
    logger.info(
        f"{params.limit} {filter_str}workflows requested; {len(results_full_list)} {filter_str}workflows found."
    )

    if all_found:
        logger.info(f"The are no remaining {filter_str}workflows to be found.")
    else:
        logger.info(
            f"There may be remaining {filter_str}workflows not included in this aggregation."
        )

    return results_full_list, pipeline_config


def attempt_error_diagnosis(api_request: dict) -> None:
    reason = _get(api_request, "error")
    message = _get(api_request, "message")
    status = _get(api_request, "statusCode")
    logger.error(
        f"Download failed. Status: {status}; reason: {reason}; message: {message}"
    )


def get_pipeline_config(params: GetSourceFilesParameters) -> dict:
    if "v3.1" not in params.platform_version:
        api_endpoint = "pipeline"
        pipeline_url = make_url(params, api_endpoint)
        return fetch_results(pipeline_url, params, api_endpoint)
    else:
        # TDP 3.1 compatibility: v3.1.* does not have a pipeline API endpoint, so we must instead fetch a single workflow to get pipeline parameters.
        api_endpoint = "workflow/workflows"
        pipeline_url = make_url(params, api_endpoint, page=1, page_size=1, status="")
        try:
            return fetch_results(pipeline_url, params, api_endpoint)[0]
        except Exception:
            return None


def fetch_results(
    url: str, params: GetSourceFilesParameters, api_endpoint="workflow"
) -> list:
    """
    Performs API call to TDP to get results.

    Args:
        url (str): URL to make API call to
        params (GetSourceFilesParameters): user-set parameters

    Returns:
        (list): list of dicts of pipeline logs
    """
    # retrieve results via API call
    headers = {
        "ts-auth-token": params.user_token,
        "x-org-slug": params.org_slug,
    }
    api_request = get(
        url, headers=headers, verify=params.verify_ssl, timeout=API_REQUEST_TIMEOUT
    ).json()

    if "statusCode" in api_request and _get(api_request, "statusCode") != 200:
        attempt_error_diagnosis(api_request)
        logger.error("API request failed!")
        return None

    if "v3.1" in params.platform_version or api_endpoint == "pipeline":
        return api_request
    else:
        # "workflow/search" has additional nesting in json
        return _get(api_request, "hits")


def make_url(
    parameters: GetSourceFilesParameters,
    api_endpoint: str,
    page: int = 0,
    page_size=100,
    status=None,
) -> str:
    """
    Returns a url for the API call based on the specified parameters and platform version numbers.

    Args:
        parameters (GetSourceFilesParameters): default parameters set by user
        api_endpoint (str): API endpoint for the query
        page (int): page number for retrieving results with pagination.

    Returns:
        (str): Complete URL for making an API call
    """

    if api_endpoint == "pipeline":
        if "v3.1" not in parameters.platform_version:
            return f"{parameters.url}pipeline/{parameters.pipeline_id}"
        else:
            return None
    else:
        base_url = f"{parameters.url}{api_endpoint}"

    def append_search_criterion(keyword: str, parameter):
        # Appends search parameters onto the API URL in this def
        nonlocal base_url
        connector = "&" if "?" in base_url else "?"
        base_url += f"{connector}{keyword}={parameter}"

    append_search_criterion("pipelineId", parameters.pipeline_id)

    # allow the filter to be different from specified if needed, e.g. for getting a single workflow for v3.1 to get pipeline info
    if status is None:
        append_search_criterion("filter", parameters.filter.lower())
    elif status == "":
        pass
    else:
        append_search_criterion("filter", status)

    if parameters.use_latest_pipeline and "v3.1" not in parameters.platform_version:
        # determine if specified start datetime is more recent:
        initial_time = determine_latest_date_from_strings(
            parameters.updated_time, parameters.start_datetime
        )
        append_search_criterion("startTime", initial_time)
    elif parameters.start_datetime:
        append_search_criterion("startTime", parameters.start_datetime)

    if parameters.end_datetime:
        append_search_criterion("endTime", parameters.end_datetime)

    if "v3.1" in parameters.platform_version:
        append_search_criterion("page", page)
        append_search_criterion("limit", page_size)
    else:
        append_search_criterion("from", page)
        append_search_criterion("size", page_size)

    return base_url


def determine_latest_date_from_strings(date_str1: str, date_str2: str) -> str:
    """
    Returns the most recent date[time] by comparing dates on a strictly lexicographical order, without trying to confirm whether either is even a valid date[time].
    Included mainly as a placeholder in case more specific functionality is needed at a later time.
    This method works as long as the largest intervals are listed first (e.g. YYYY-MM-DD), and leading zeros are not dropped (e.g. use 2022-01-02, not 2022-1-2).

    Args:
        date_str1 (str): first datetime as a string
        date_str1 (str): second datetime as a string

    Returns:
        str: later datetime based on a lexicographical ordering of dates
    """
    if not date_str1:
        return date_str2
    if not date_str2:
        return date_str1
    return date_str1 if date_str1 > date_str2 else date_str2


def save_raw_file_ids(
    errors: list, file_ids: list, params: GetSourceFilesParameters
) -> None:
    output_path = os.path.join(params.save_dir, f"{params.raw_file_name}.txt")
    logger.info(f"Saving file ID list to {output_path}")
    logger.debug(f"Full output path for file IDs: {os.path.abspath(output_path)}")
    if params.truncate_raw_file_ids != -1:
        logger.info(
            f"Truncating file ID list for each file type to  {params.truncate_raw_file_ids} IDs."
        )
        file_ids = []
        for error in errors:
            count = 0
            while count < params.truncate_raw_file_ids:
                try:
                    file_id = _get(error, "workflow_info")[count][3]
                    count += 1
                    file_ids.append(file_id)
                except IndexError as err:
                    logger.debug(
                        f"Ending file ID list early for error because only {count} file IDs found for this error."
                    )
                    break
    with open(output_path, "wt") as fout:
        fout.write("\n".join(file_ids))


def main():

    command_line_parser = WeaArgParser()
    command_line_parser.parser_setup(WorkflowErrorAggregatorParameters())
    params = command_line_parser.parse_input_args()

    configure_logging(root=params.log_root)
    log_parameters(params)

    # attempt to make output folder if it doesn't exist
    if not os.path.isdir(params.save_dir):
        try:
            os.mkdir(params.save_dir)
            logger.info(f"Files will be saved to {params.save_dir}.")
        except OSError as exc:
            logger.error(
                f"Directory {params.save_dir} cannot be created. Bombing out..."
            )
            exit()

    # get workflows
    response, pipeline_config = get_pipeline_info(params)

    if not response:
        return

    if isinstance(response, dict) and response["error"]:
        logger.info(response)
        return

    workflows = response
    if len(workflows) == 0:
        logger.info("No workflow found with given condition")
        return

    # aggregate errors
    latest_wfs = filter_latest_workflow(workflows, params)
    if not latest_wfs:
        return
    workflow_df = workflow_result_to_dataframe(
        latest_wfs,
        task_result_message="tasks.-1.output.result.message",
    )

    if params.csv_output_name:
        workflow_df[
            [
                "id",
                "createdAt",
                "lastUpdatedAt",
                "file_id",
                "task_result_message",
            ]
        ].to_csv(f"{params.csv_output_name}.csv")

    errors, file_id_list = aggregate_workflow_errors(
        workflow_df, params.similarity_ratio, status=params.filter
    )

    # summary report
    msg = "error" if params.filter.lower() == "failed" else "message"

    logger.info(
        f"With similarity ratio: {params.similarity_ratio}, the unique {msg} count is: {len(errors)}, distribution:"
    )
    for index, existing_err in enumerate(errors):
        count = existing_err["count"]
        logger.info(f"Index: {index}, Count: {count}")

    # save raw file IDs to a file

    if params.raw_file_name:
        save_raw_file_ids(errors, file_id_list, params)

    if params.html_output_name:
        make_html_output(errors, params, pipeline_config)


if __name__ == "__main__":
    main()
