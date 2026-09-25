from pathlib import Path

import metscore
import streamlit as st
from metscore.files import read_table

from ui import (
    render_breadcrumb,
    render_download_controls,
    render_individual_result,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DATA_CSV = PROJECT_ROOT / "examples" / "example_data.csv"
EXAMPLE_DATA_XLSX = PROJECT_ROOT / "examples" / "example_data.xlsx"


def reset_tabular_navigation() -> None:
    st.session_state.selected_result_row = None
    st.session_state.pop("tabular_results_table", None)


def reset_tabular_workflow() -> None:
    reset_tabular_navigation()
    st.session_state.tabular_uploader_version += 1
    st.session_state.pop("tabular_use_example", None)


def handle_tabular_upload_change() -> None:
    reset_tabular_navigation()
    st.session_state.tabular_use_example = False


def activate_tabular_example() -> None:
    reset_tabular_navigation()
    st.session_state.tabular_use_example = True


def render_process_another_dataset_button() -> None:
    st.button(
        "Process another dataset",
        type="secondary",
        width="stretch",
        on_click=reset_tabular_workflow,
    )


def render_tabular_workflow() -> None:
    title_col, back_col = st.columns(
        [5, 1.5],
        vertical_alignment="center",
    )

    with title_col:
        st.html('<p class="input-label">Tabular data</p>')

    with back_col:
        if st.button(
            "← Change input type",
            width="stretch",
        ):
            st.session_state.input_mode = None
            reset_tabular_workflow()
            st.rerun()

    st.subheader("Upload tabular data")

    st.write(
        "Upload a CSV or Excel file containing the 22 variables "
        "required by MetSCORE. Each row represents one sample."
    )

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx"],
        key=f"tabular_file_{st.session_state.tabular_uploader_version}",
        width="stretch",
        on_change=handle_tabular_upload_change,
    )

    use_example = st.session_state.get("tabular_use_example", False)

    if uploaded_file is None and not use_example:
        st.caption(
            "No file ready? Try the bundled example or download it to inspect "
            "the expected input format."
        )

        try_col, csv_col, excel_col = st.columns([1.2, 1, 1])

        with try_col:
            st.button(
                "Try example data",
                width="stretch",
                on_click=activate_tabular_example,
            )

        with csv_col:
            st.download_button(
                "Download CSV",
                data=EXAMPLE_DATA_CSV.read_bytes(),
                file_name=EXAMPLE_DATA_CSV.name,
                mime="text/csv",
                width="stretch",
                on_click="ignore",
            )

        with excel_col:
            st.download_button(
                "Download Excel",
                data=EXAMPLE_DATA_XLSX.read_bytes(),
                file_name=EXAMPLE_DATA_XLSX.name,
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch",
                on_click="ignore",
            )

    if use_example:
        source = EXAMPLE_DATA_CSV
        source_name = f"Example · {EXAMPLE_DATA_CSV.name}"
    elif uploaded_file is not None:
        source = uploaded_file
        source_name = uploaded_file.name
    else:
        return

    try:
        data = read_table(source)
    except Exception as exc:
        st.error(f"Could not read the input file: {exc}")
        return

    st.caption(
        f"✓ {source_name} · "
        f"{len(data)} sample(s) · "
        f"{len(data.columns)} input columns"
    )

    try:
        result = metscore.predict(data)
    except (TypeError, ValueError) as exc:
        st.error("The input data are not compatible with MetSCORE.")
        st.error(str(exc))

        with st.expander("Inspect input data"):
            st.dataframe(
                data,
                width="stretch",
                hide_index=True,
            )

        render_process_another_dataset_button()
        return

    output_columns = [
        "MetSCORE",
        "t_pred",
        "t_orth_1",
    ]

    display_columns = output_columns + [
        column for column in result.columns if column not in output_columns
    ]

    column_config = {
        "MetSCORE": st.column_config.NumberColumn(
            "MetSCORE",
            pinned=True,
        ),
        "t_pred": st.column_config.NumberColumn(
            "t_pred",
            pinned=True,
        ),
        "t_orth_1": st.column_config.NumberColumn(
            "t_orth_1",
            pinned=True,
        ),
    }

    if use_example:
        download_kwargs = {
            "base_name": "example_data_metscore_results",
        }
    else:
        download_kwargs = {
            "uploaded_file": uploaded_file,
        }

    if len(result) == 1:
        render_breadcrumb("Upload &nbsp;›&nbsp; <strong>Individual result</strong>")

        render_individual_result(
            result.iloc[0],
            data.iloc[[0]],
        )

        render_download_controls(
            result,
            **download_kwargs,
        )

        render_process_another_dataset_button()
        return

    selected_row = st.session_state.get("selected_result_row")

    if selected_row is None:
        render_breadcrumb("Upload &nbsp;›&nbsp; <strong>Results</strong>")

        st.markdown("### Results")

        st.caption("Click any cell in a row to inspect its individual MetSCORE.")

        event = st.dataframe(
            result[display_columns],
            width="stretch",
            hide_index=True,
            column_config=column_config,
            on_select="rerun",
            selection_mode="single-cell",
            key="tabular_results_table",
        )

        if event.selection.cells:
            selected_row = event.selection.cells[0][0]
            st.session_state.selected_result_row = selected_row
            st.rerun()

        render_download_controls(
            result,
            **download_kwargs,
        )

        render_process_another_dataset_button()
        return

    render_breadcrumb(
        "Upload &nbsp;›&nbsp; Results "
        "&nbsp;›&nbsp; <strong>Individual result</strong>"
    )

    if st.button(
        "← Back to results",
        type="tertiary",
    ):
        st.session_state.selected_result_row = None
        st.session_state.pop("tabular_results_table", None)
        st.rerun()

    render_individual_result(
        result.iloc[selected_row],
        data.iloc[[selected_row]],
    )

    render_process_another_dataset_button()
