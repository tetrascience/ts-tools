import pandas as pd
import os
from pydash import get as _get
from loguru import logger
from typing import Tuple

UNIQUE_DELINEATOR1 = "A+" * 8  # placeholder for adding html code
UNIQUE_DELINEATOR2 = "B-" * 8  # placeholder for adding html code
UNIQUE_DELINEATOR_LT = "C^" * 8  # placeholder for adding html code
UNIQUE_DELINEATOR_GT = "D~" * 8  # placeholder for adding html code
OMIT_CREATION_TIME = True


def make_monospace_type(size: float = 80) -> Tuple[str, str]:
    start = f"{UNIQUE_DELINEATOR_LT}font style='font-family:\"Courier New\", Courier, monospace; font-size:{size}%'{UNIQUE_DELINEATOR_GT}"
    end = f"{UNIQUE_DELINEATOR_LT}/font{UNIQUE_DELINEATOR_GT}"
    return start, end


def make_html_output(errors: dict, params, pipeline_config: dict) -> None:
    """
    Creates the html output for the aggregated workflow errors.
    """
    # export to Pandas dataframe and export but make the it *~pretty~*.

    def clean_errors():
        nonlocal errors
        for ind, error_list in enumerate(errors):
            # get the workflow error looking nice
            start, end = make_monospace_type()
            error = str(_get(errors[ind]["value"], "result.message"))
            if not error:
                error = str(errors[ind]["value"])
            error_value = start + error + end
            error_value = error_value.replace("\n", UNIQUE_DELINEATOR1)
            error_value = error_value.replace("  ", UNIQUE_DELINEATOR2)
            errors[ind]["value"] = error_value

            # Put each failed workflow on its own line
            errors[ind]["workflow_info"] = UNIQUE_DELINEATOR1.join(
                [make_file_links(a) for a in error_list["workflow_info"]]
            )

            # add monospace type to this part
            errors[ind]["workflow_info"] = start + errors[ind]["workflow_info"] + end

    def make_file_links(workflow_line: str) -> str:
        nonlocal params

        def make_html_link(url: str, text: str) -> str:
            return f'{UNIQUE_DELINEATOR_LT}a href="{url}", target="_blank"{UNIQUE_DELINEATOR_GT}{text}{UNIQUE_DELINEATOR_LT}/a{UNIQUE_DELINEATOR_GT}'

        if not params.env_url:
            params.env_url = params.url.replace("//api.", "//").replace("/v1/", "/")
        wf_link = params.env_url + "workflows/" + workflow_line[0]
        fid_link = (
            params.env_url
            + "file-details/"
            + workflow_line[3]
            + "?pipelineId="
            + workflow_line[0]
        )
        line_with_links = f"{make_html_link(wf_link, workflow_line[0])}"
        if not OMIT_CREATION_TIME:
            line_with_links += f": {workflow_line[1]}"
        line_with_links += f", {workflow_line[2]}"
        line_with_links += f", {make_html_link(fid_link, 'raw file')}"
        return line_with_links

    clean_errors()

    error_df = pd.DataFrame(errors)  # convert to dataframe

    output_path = os.path.join(params.save_dir, f"{params.html_output_name}.html")
    tmp_path = os.path.join(params.log_root, "tmp.html")
    error_df.to_html(tmp_path, col_space=[512, 32, 520], justify="left")
    with open(tmp_path, "rt") as fin:
        with open(output_path, "wt") as fout:
            fout.write(
                make_html_header(
                    pipeline_config,
                    version=params.platform_version,
                    status=params.filter,
                )
            )
            for line in fin:
                fout.write(make_html_line(line, status=params.filter))
    os.remove(tmp_path)
    logger.info(
        f"Detailed aggregated workflow and count table is saved to {output_path}"
    )
    logger.debug(
        f"Full output path for aggregated workflow and count table html: {os.path.abspath(output_path)}"
    )


def make_html_line(line: str, status="failed") -> str:
    if status.lower() == "failed":
        value = "Error Message"
        wf_replace = "Failed "
    else:
        value = "Message"
        wf_replace = ""

    replacements = {
        UNIQUE_DELINEATOR1: "<br>",
        UNIQUE_DELINEATOR2: "&nbsp;" * 2,
        UNIQUE_DELINEATOR_LT: "<",
        UNIQUE_DELINEATOR_GT: ">",
        "value": value,
        "count": "Count",
        "<tr>": r'<tr style="text-align: left; vertical-align: top;">',
    }

    if OMIT_CREATION_TIME:
        replacements[
            "workflow_info"
        ] = f"{wf_replace}Workflows (workflow ID, last update time, raw file ID)"
    else:
        replacements[
            "workflow_info"
        ] = f"{wf_replace}Workflows (workflow ID, creation time, last update time, raw file ID)"
    for k, v in replacements.items():
        line = line.replace(k, v)
    return line


def make_html_header(pipeline_config: dict, version="v3.3", status="failed") -> str:
    if "v3.1" in version:
        included_pipeline_params = {
            "Pipeline Name": "protocol.name",
            "Pipeline ID": "id",
            "Description": "protocol.description",
            "Protocol Slug": "protocolSlug",
            "Protocol Version": "protocolVersion",
            "Master Script Slug": "masterScriptSlug",
            "Master Script Version": "masterScriptVersion",
            "Pipeline Configuration": "pipelineConfig",
        }
    else:
        included_pipeline_params = {
            "Pipeline Name": "name",
            "Pipeline ID": "id",
            "Description": "description",
            "Protocol Slug": "protocolSlug",
            "Protocol Version": "protocolVersion",
            "Pipeline Creation Date/Time": "createdAt",
            "Pipeline Update Date/Time": "updatedAt",
            "Master Script Slug": "masterScriptSlug",
            "Master Script Version": "masterScriptVersion",
            "Pipeline Configuration": "pipelineConfig",
        }

    def make_pretty_pipeline_config(title, config: dict, indent=1) -> str:
        if not config:
            return "None"
        else:
            list = []
            for k, v in config.items():
                if type(v) is dict:
                    v = make_pretty_pipeline_config(k, v, indent=indent + 1)
                list.append(f"{k}: {v}")
            indent_str = f"<br>{'&nbsp;' * 4 * indent}"
            return f"{title}:{indent_str}" + indent_str.join(list)

    if status.lower() == "failed":
        header = "<h1>Workflow Error Aggregator</h1>\n<p>"
    else:
        header = "<h1>Workflow Aggregator</h1>\n<p>"

    header += f"Workflow Status: {status}<br>\n"
    for k, v in included_pipeline_params.items():
        if v == "pipelineConfig":
            header += make_pretty_pipeline_config(k, _get(pipeline_config, v)) + "\n"
        else:
            header += f"{k}: {_get(pipeline_config, v)}<br>\n"
    return header + "</p> \n"
