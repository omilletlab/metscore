import metscore
import streamlit as st
from metscore.files import read_table

from ui import (
    render_breadcrumb,
    render_download_controls,
    render_individual_result,
)


def reset_tabular_navigation() -> None:
    st.session_state.selected_result_row = None
    st.session_state.pop("tabular_results_table", None)


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
            reset_tabular_navigation()
            st.session_state.pop("tabular_file", None)
            st.rerun()

    st.subheader("Upload tabular data")

    st.write(
        "Upload a CSV or Excel file containing the 22 variables "
        "required by MetSCORE. Each row represents one sample."
    )

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx"],
        key="tabular_file",
        width="stretch",
        on_change=reset_tabular_navigation,
    )

    if uploaded_file is None:
        return

    try:
        data = read_table(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read the uploaded file: {exc}")
        return

    st.caption(
        f"✓ {uploaded_file.name} · "
        f"{len(data)} sample(s) · "
        f"{len(data.columns)} input columns"
    )

    try:
        result = metscore.predict(data)
    except (TypeError, ValueError) as exc:
        st.error("The uploaded data are not compatible with MetSCORE.")
        st.error(str(exc))

        with st.expander("Inspect uploaded data"):
            st.dataframe(
                data,
                width="stretch",
                hide_index=True,
            )

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

    if len(result) == 1:
        render_breadcrumb("Upload &nbsp;›&nbsp; <strong>Individual result</strong>")

        render_individual_result(
            result.iloc[0],
            data.iloc[[0]],
        )

        render_download_controls(
            result,
            uploaded_file,
        )

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
            uploaded_file,
        )

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
