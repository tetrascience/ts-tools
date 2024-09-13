# Workflow Error Aggregator

The workflow error aggregator (WEA) script will search for workflows of a given pipeline ID and aggregate all the errors, so you can easily tell how many unique error there are and the count of each error type.
Output may include the aggregated errors, as well as the file IDs for the raw files that failed the workflow.

The WEA can also be used for non-failed workflows by setting `STATUS` to `"completed"`, `"pending"`, or `"in progress"`. In this case, aggregation still occurs, but is based on the success message.

## Output

This program has the option to create an html file with the aggregated workflow \[error\] messages, the number of workflows that had that \[error\] message, and the workflow and raw file IDs that match that \[error\] message.
The workflow IDs and raw file IDs in this html output include hyperlinks to the workflow/file in the platform if the user is currently logged in to the platform.

There is also the option to produce a list of raw file IDs for failed workflows.
The user may specify a maximum number of file IDs to save to the output file for each error using the `TRUNCATE_RAW_FILE_IDS` parameter; this may be useful if the intent is to download a sample of files for each \[error\] message type for debugging purposes, with, for example, the `bulk-file-downloader`.
Alternatively, setting `TRUNCATE_RAW_FILE_IDS` to `-1` will save all the file IDs to this file if the intent is to produce a list of files for reprocessing.

## How to Use

1. Install Python dependencies `poetry install`
2. Fill in the configuration in `defaultparams.py`
3. Run `poetry run python workflow_error_aggregator.py` with desired command line arguments:

```[bash]
workflow_error_aggregator [-h] [-p PIPELINE_ID] [-u BASE_URL] [-E ENV_URL] [-t USER_TOKEN] [-o ORG_SLUG] [-l LIMIT] [-f FILTER] [-z SIMILARITY_RATIO] [-b START_DATETIME] [-e END_DATETIME] [-S VERIFY_SSL] [-q] [-Q PROTOCOL_VERSION] [-P] [-v PLATFORM_VERSION] [-s SAVE_DIR] [-r RAW_FILE_NAME] [-H HTML_OUTPUT_NAME] [-C CSV_OUTPUT_NAME] [-L LOG_ROOT] [-T TRUNCATE_RAW_FILE_IDS]
```

## Configuration Parameters

Short Flag | Long Flag | Parameter | Type | Description
--- | --- | --- | --- | ---
`-p` | `--pipeline-id` | `PIPELINE_ID` | `str` | Pipeline ID for the pipeline of interest. Obtained from TDP
`-u` | `--url` | `BASE_URL` | `str` | TDP URL. For tetrascience UAT, this value is `"https://api.tetrascience-uat.com/v1/"`
`-E` | `--env-url` | `ENV_URL` | `str` | Set the environment/TDP url. For tetrascience UAT, this value is `"https://tetrascience-uat.com/"`. If used, this url is used to make links in the output HTML file to the workflows and raw file IDs. If left empty or set to `None`, then the url is extrapolated from the `BASE_URL` by removing `api.` and `v1/`.
`-t` | `--token` | `TS_AUTH_TOKEN` | `str` | Authorization token for access to the TDP
`-o` | `--org-slug` | `X_ORG_SLUG` | `str` | Organization slug for the environment
`-l` | `--limit` | `LIMIT` | `int` > 0 | Limit for number of workflows that should be fetched.
`-f` | `--filter` | `FILTER` | `str` | A filter for status for the workflow. For failed files, this should be set to `"failed"`; however, this could also be set to `"pending"` or `"completed"` for those respective files.
`-z` | `--sim-ratio` | `SIMILARITY_RATIO` | `float` between 0 and 1 | Similarity ratio for error messages. Must be between 0 and 1, inclusive. If set to 1, then error messages that differ will produce separate groups of aggregated of data.
`-b` | `--begin` | `START_DATETIME` | `str` | Earliest date/time for the file search. Valid formats are specified below.
`-e` | `--end` | `END_DATETIME` | `str` | Latest date/time for the file search. Valid formats are specified below.
`-S` | `--ssl` | `VERIFY_SSL` | `bool` flag | If set to `True`, SSL verification is performed for API calls.
`-q` | `--latest-protocol` | `USE_LATEST_PROTOCOL` | `bool` flag | If true, results are filtered based on the version number of the current protocol number of for the version pipeline. This behavior only works for TDP v3.2.\* and later. For TDP v3.1.\*, `PROTOCOL_VERSION` must be specified. If `USE_LATEST_PROTOCOL` is `True` and `PROTOCOL_VERSION` is specified for TDP v3.2.\* and later, the `USE_LATEST_PROTOCOL` flag takes precedence.
`-Q` | `--protocol-version` | `PROTOCOL_VERSION` | `str` | Specified protocol version to match for errors.  Must be prefaced with "v", e.g. `"v3.2.3"` or `v3.2`. If `USE_LATEST_PROTOCOL` is `True` and `PROTOCOL_VERSION` is specified for TDP v3.2.\* and later, the `USE_LATEST_PROTOCOL` flag takes precedence.
`-P` | `--latest-pipeline` | `USE_LATEST_PIPELINE` | `bool` flag | If true, results are filtered based on the timestamp of the last pipeline update or `START_DATETIME`, whichever is later. Note that this automatically ensures the use of the latest protocol. This behavior only works for TDP v3.2.* and later.
`-v` | `--version` | `PLATFORM_VERSION` | `str` | Version number of the TDP platform. Must be prefaced with "v", e.g. `"v3.2.3"` or `v3.2`. (Note that the API only changes with major and minor updates; build number does not change the API.)
`-L` | `--log-root` | `LOG_ROOT` | `str` directory path | Sets the base directory for log files from the program. Must be an existing directory.
`-s` | `--save-dir` | `SAVE_DIR` | `str` directory path | Path to save directory. Cannot be more than one level deeper than an existing directory.
`-r` | `--raw-output` | `RAW_FILE_NAME` | `str` | File name of the list of the raw file ids. Should not contain the extension or path. If set to `None` or `""` (empty string), then no file is generated.
`-H` | `--html-output` | `HTML_OUTPUT_NAME` | `str` | File name of html output file of the aggregated workflow errors. Should not contain the extension or path. If set to `None` or `""` (empty string), then no file is generated.
`-C` | `--csv-output` | `CSV_OUTPUT_NAME` | `str` | File name of csv output file of the aggregated workflow errors. Should not contain the extension or path. If set to `None` or `""` (empty string), then no file is generated.
`-T` | `--truncate` | `TRUNCATE_RAW_FILE_IDS` | `int` >= 1 or == -1 | Number of file IDs to print for a given aggregated error. If set to -1, then all file IDs are printed. This is useful for limiting the number of file IDs printed to the `RAW_FILE_NAME` file if a sample of raw files for each error is to be downloaded.

### Time Formats

Valid formats for the time are:

- `"YYYY-MM-DDTHH:MM:SS"`, e.g. `"2022-11-02T13:38:00"`, or
- `"YYYY-MM-DD"`, e.g. `"2022-11-02`. The default time in this case is set to `00:00:00`.

The WEA does not perform any checking to ensure this value matches the required format.

## Notes

- When the WEA is used with a `FILTER` other than `"failed"`, the messages used to aggregate the workflows is unlikely to be particularly useful, except perhaps for determining result type (e.g. `s3file`) or bucket (e.g. `ts-dip-uat-datalake`).
- The `LIMIT` parameter is used when performing the API call to TDP to retrieve a list of files matching the other search requirements. The number of retrieved files may be less that `LIMIT` if:
  - there are fewer files than `LIMIT` that match other search criteria (e.g. `FILTER`, `START_DATETIME`), or
  - there are at least `LIMIT` files matching the criteria, but some are removed due to:
    - the use of `USE_LATEST_PROTOCOL` keyword, which may remove some results from previous protocol versions, and/or
    - some duplicated workflows are returned from the same protocol/pipeline version, and duplicates are removed. This may occur if a workflow has been submitted and failed multiple times with the same pipeline configuration.
- If a `START_DATETIME` is specified and `USE_LATEST_PIPELINE` is also specified, the two dates are compared using a lexicographical ordering, with the later datetime taking precedence.
- `PLATFORM_VERSION` is required because v3.1.\* versions of TDP do not have access to the "workflow/search" API, and must use "workflow/workflows", which is deprecated in later versions.
  - For v3.2 and later, the "workflow/search" API endpoint is used. This call returns as most 100 results, and pagination is used. This requires ceil(`LIMIT`/100) API calls to be made to retrieve the results.
  - Pipelines that have workflows with changing status (e.g. moving from in progress or queued to failed or completed) change the pagination of results, which may result in unexpected behavior of the workflow error aggregator (e.g. missed or duplicated workflows). For best results, use the WEA when there are no pending/in-progress workflows.
- The APIs to retrieve workflow data for TDP >=v3.2.\* allow a maximum of 100 workflows per page. For TDP v3.1.\*, this limit is not given; however, for the default is still set to 100. For pipelines that have large (more then approximately 10,000) workflows, this limit may still be too high, and the slower APIs will
- In TDP v3.1.\*, there is no `"/pipelines"` API, so neither the most recent pipeline update time nor the protocol version are available, and thus `USE_LATEST_PROTOCOL` and `USE_LATEST_PIPELINE` are ignored for these early platform versions. Instead, the `PROTOCOL_VERSION` may be specified to look only for workflows that match that version, and `START_DATETIME` may be set to after the most recent update time of the pipeline.
- To speed up the program when many types of errors are present, the length of the error message being compared when the `SIMILARITY_RATIO` is not 1 is truncated. The length of the truncation is set with the `ERROR_MESSAGE_TRUNCATION_LENGTH` constant, which is found in `aggregate_workflow_errors.py`. Comparing strings with performed with `SequenceMatcher`, which is linear w.r.t. string length on average case but quadratic on worst case. This behavior may be too slow with full messages with large numbers of messages and message groups, which is why `ERROR_MESSAGE_TRUNCATION_LENGTH` may be changed.
