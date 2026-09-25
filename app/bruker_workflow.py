from pathlib import Path
from tempfile import TemporaryDirectory

import metscore
import streamlit as st

from ui import (
    render_breadcrumb,
    render_download_controls,
    render_individual_result,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_BRUKER_DIR = PROJECT_ROOT / "examples" / "bruker"
EXAMPLE_METABOLITES_XML = EXAMPLE_BRUKER_DIR / "sample_001_metabolites.xml"
EXAMPLE_LIPOPROTEINS_XML = EXAMPLE_BRUKER_DIR / "sample_001_lipoproteins.xml"


def reset_bruker_workflow() -> None:
    st.session_state.bruker_uploader_version += 1
    st.session_state.pop("bruker_use_example", None)


def activate_bruker_example() -> None:
    st.session_state.bruker_use_example = True


def handle_bruker_upload_change() -> None:
    st.session_state.bruker_use_example = False


def render_bruker_workflow() -> None:
    title_col, back_col = st.columns(
        [5, 1.5],
        vertical_alignment="center",
    )

    with title_col:
        st.html('<p class="input-label">Bruker XML</p>')

    with back_col:
        if st.button(
            "← Change input type",
            width="stretch",
            key="bruker_change_input",
        ):
            st.session_state.input_mode = None
            st.session_state.pop("bruker_use_example", None)
            st.session_state.pop("bruker_files", None)
            st.rerun()

    st.subheader("Upload Bruker reports")

    st.write(
        "Upload the metabolite and lipoprotein XML reports for one sample. "
        "The files may be provided in either order."
    )

    uploaded_files = st.file_uploader(
        "Choose two XML files",
        type=["xml"],
        accept_multiple_files=True,
        key=f"bruker_files_{st.session_state.bruker_uploader_version}",
        width="stretch",
        on_change=handle_bruker_upload_change,
    )

    use_example = st.session_state.get("bruker_use_example", False)

    if not uploaded_files and not use_example:
        st.caption(
            "No files ready? Try the bundled example or download the reports "
            "to inspect the expected input format."
        )

        try_col, metabolites_col, lipoproteins_col = st.columns([1.1, 1.3, 1.3])

        with try_col:
            st.button(
                "Try example",
                width="stretch",
                on_click=activate_bruker_example,
            )

        with metabolites_col:
            st.download_button(
                "Download metabolites",
                data=EXAMPLE_METABOLITES_XML.read_bytes(),
                file_name=EXAMPLE_METABOLITES_XML.name,
                mime="application/xml",
                width="stretch",
                on_click="ignore",
            )

        with lipoproteins_col:
            st.download_button(
                "Download lipoproteins",
                data=EXAMPLE_LIPOPROTEINS_XML.read_bytes(),
                file_name=EXAMPLE_LIPOPROTEINS_XML.name,
                mime="application/xml",
                width="stretch",
                on_click="ignore",
            )

    if use_example:
        st.caption(
            f"✓ Example · {EXAMPLE_METABOLITES_XML.name} · "
            f"{EXAMPLE_LIPOPROTEINS_XML.name}"
        )

        try:
            result = metscore.predict_bruker_files(
                EXAMPLE_METABOLITES_XML,
                EXAMPLE_LIPOPROTEINS_XML,
            )
        except Exception as exc:
            st.error("The example Bruker reports could not be processed.")
            st.error(str(exc))
            return

    else:
        if not uploaded_files:
            return

        if len(uploaded_files) != 2:
            st.warning(
                "MetSCORE requires exactly two Bruker XML reports: "
                "one metabolite report and one lipoprotein report."
            )
            return

        st.caption(f"✓ {uploaded_files[0].name} · {uploaded_files[1].name}")

        try:
            with TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)

                first_path = temp_dir / "first.xml"
                second_path = temp_dir / "second.xml"

                first_path.write_bytes(uploaded_files[0].getvalue())
                second_path.write_bytes(uploaded_files[1].getvalue())

                result = metscore.predict_bruker_files(
                    first_path,
                    second_path,
                )

        except Exception as exc:
            st.error("The Bruker reports could not be processed.")
            st.error(str(exc))
            return

    render_breadcrumb("Upload &nbsp;›&nbsp; <strong>Individual result</strong>")

    output_columns = [
        "MetSCORE",
        "t_pred",
        "t_orth_1",
    ]

    input_data = result[
        [column for column in result.columns if column not in output_columns]
    ]

    render_individual_result(
        result.iloc[0],
        input_data,
    )

    sample_name = str(
        result.iloc[0].get(
            "sample_id",
            "bruker_sample",
        )
    )

    render_download_controls(
        result,
        base_name=f"{sample_name}_metscore_results",
    )

    st.button(
        "Process another sample",
        type="secondary",
        width="stretch",
        on_click=reset_bruker_workflow,
    )
