from tempfile import TemporaryDirectory

import math

from io import BytesIO

import metscore
from metscore.files import read_table

from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "assets" / "omilletlab-logo.png"


def reset_bruker_workflow() -> None:
    st.session_state.bruker_uploader_version += 1


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
    )

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
        st.error("The uploaded Bruker reports could not be processed.")
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

    sample_name = str(result.iloc[0].get("sample_id", "bruker_sample"))

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


def reset_tabular_navigation() -> None:
    st.session_state.selected_result_row = None
    st.session_state.pop("tabular_results_table", None)


def render_breadcrumb(text: str) -> None:
    st.html(f"""
        <div style="
            color:#66727d;
            font-size:0.82rem;
            margin:0.2rem 0 0.8rem 0;
        ">
            {text}
        </div>
        """)


def render_individual_result(row, input_row) -> None:
    score = float(row["MetSCORE"])
    score = max(0.0, min(1.0, score))
    score_pct = score * 100

    st.html(f"""
        <div style="
            max-width:680px;
            margin:0 0 1rem 0;
            border:1px solid #dce5ea;
            border-radius:14px;
            padding:1.1rem 1.2rem 1.2rem 1.2rem;
            background:#ffffff;
        ">
            <div style="
                color:#66727d;
                font-size:0.88rem;
                margin-bottom:0.2rem;
            ">
                MetSCORE
            </div>

            <div style="
                color:#17212b;
                font-size:3rem;
                font-weight:700;
                line-height:1;
                margin-bottom:1rem;
            ">
                {score:.3f}
            </div>

            <div style="
                position:relative;
                padding-top:1.9rem;
                margin-top:0.3rem;
            ">
                <div style="
                    position:absolute;
                    left:{score_pct}%;
                    top:0;
                    transform:translateX(-50%);
                    background:#17212b;
                    color:white;
                    font-size:0.78rem;
                    font-weight:600;
                    padding:0.22rem 0.5rem;
                    border-radius:999px;
                    white-space:nowrap;
                ">
                    {score:.3f}
                </div>

                <div style="
                    position:relative;
                    height:18px;
                    border-radius:999px;
                    background:linear-gradient(
                        90deg,
                        #2ca25f 0%,
                        #9fd36a 25%,
                        #f1d04b 50%,
                        #f39c34 75%,
                        #cf3e3e 100%
                    );
                ">
                    <div style="
                        position:absolute;
                        left:50%;
                        top:-7px;
                        width:2px;
                        height:32px;
                        background:#17212b;
                        opacity:0.45;
                    "></div>

                    <div style="
                        position:absolute;
                        left:{score_pct}%;
                        top:-6px;
                        transform:translateX(-50%);
                        width:0;
                        height:0;
                        border-left:7px solid transparent;
                        border-right:7px solid transparent;
                        border-bottom:12px solid #17212b;
                    "></div>
                </div>

                <div style="
                    display:grid;
                    grid-template-columns:1fr 1fr 1fr;
                    margin-top:0.55rem;
                    font-size:0.8rem;
                    color:#66727d;
                ">
                    <div style="text-align:left;">
                        <strong style="color:#17212b;">Asymptomatic</strong><br>
                        0
                    </div>

                    <div style="text-align:center;">
                        <strong style="color:#17212b;">Threshold</strong><br>
                        0.5
                    </div>

                    <div style="text-align:right;">
                        <strong style="color:#17212b;">MetS</strong><br>
                        1
                    </div>
                </div>
            </div>
        </div>
        """)

    with st.expander("Input data"):
        st.dataframe(
            input_row,
            width="stretch",
            hide_index=True,
        )

    with st.expander("Technical details"):
        technical = row[["t_pred", "t_orth_1"]].to_frame().T

        st.dataframe(
            technical,
            width="stretch",
            hide_index=True,
        )


def render_download_controls(
    result,
    uploaded_file=None,
    base_name: str | None = None,
) -> None:
    download_format = st.radio(
        "Download format",
        options=["CSV", "Excel"],
        horizontal=True,
        key="tabular_download_format",
    )

    if base_name is None:
        base_name = f"{Path(uploaded_file.name).stem}_metscore_results"

    if download_format == "CSV":
        download_data = result.to_csv(index=False).encode("utf-8")
        download_name = f"{base_name}.csv"
        download_mime = "text/csv"

    else:
        excel_buffer = BytesIO()

        result.to_excel(
            excel_buffer,
            index=False,
            engine="openpyxl",
        )

        download_data = excel_buffer.getvalue()
        download_name = f"{base_name}.xlsx"
        download_mime = (
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
        )

    st.download_button(
        label="Download results",
        data=download_data,
        file_name=download_name,
        mime=download_mime,
        width="stretch",
        on_click="ignore",
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


def set_input_mode(mode: str) -> None:
    st.session_state.input_mode = mode


if "input_mode" not in st.session_state:
    st.session_state.input_mode = None

if "selected_result_row" not in st.session_state:
    st.session_state.selected_result_row = None

if "bruker_uploader_version" not in st.session_state:
    st.session_state.bruker_uploader_version = 0


st.set_page_config(
    page_title="MetSCORE",
    layout="wide",
)

st.html("""
    <style>
    :root {
        --text: #17212b;
        --text-muted: #66727d;
        --primary: #2479a8;
        --primary-dark: #195b80;
        --primary-soft: #eaf4f9;
        --border: #dce5ea;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    h3 {
        color: var(--text);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--border);
        border-radius: 12px;
    }

    .input-label {
        color: var(--primary);
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .header-links {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 0.6rem;
    }

    .header-links a {
        color: var(--primary);
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.4rem 0.75rem;
        border: 1px solid var(--border);
        border-radius: 999px;
        background: white;
    }

    .header-links a:hover {
        color: var(--primary-dark);
        border-color: var(--primary);
        background: var(--primary-soft);
    }

    .app-intro {
        margin: 0;
        padding: 0;
    }

    .app-divider {
        border-top: 1px solid var(--border);
        margin: 0.45rem 0 1.25rem 0;
    }

    .app-intro h1 {
        color: var(--text);
        font-size: clamp(2.7rem, 5vw, 4rem);
        line-height: 1;
        letter-spacing: -0.05em;
        margin: 0 0 0.75rem 0;
        padding: 0;
    }

    .app-intro p {
        color: var(--text);
        margin: 0 0 0.9rem 0;
        padding: 0;
    }
    </style>
    """)

# Header
logo_col, identity_col, links_col = st.columns(
    [0.9, 5.8, 2.3],
    vertical_alignment="center",
)

with logo_col:
    st.image(
        LOGO_PATH,
        width=88,
    )

with identity_col:
    st.html("""
        <div style="line-height:1.35;">
            <div style="
                color:#17212b;
                font-weight:700;
                font-size:0.95rem;
                margin-bottom:0.25rem;
            ">
                Precision Medicine &amp; Metabolism Lab
            </div>
            <a
                href="https://www.cicbiogune.es/"
                target="_blank"
                style="
                    color:#66727d;
                    font-size:0.82rem;
                    text-decoration:none;
                "
            >
                CIC bioGUNE
            </a>
        </div>
        """)

with links_col:
    st.html("""
        <div class="header-links">
            <a href="https://www.omilletlab.com/" target="_blank">
                Lab website
            </a>
            <a href="https://github.com/omilletlab/metscore" target="_blank">
                GitHub
            </a>
        </div>
        """)

st.html("""
    <div class="app-intro">
        <div class="app-divider"></div>

        <h1>MetSCORE</h1>

        <p>
            Calculate and explore a serum NMR metabolomics-based metric
            for metabolic syndrome.
        </p>
    </div>
    """)

# Input workflow
if st.session_state.input_mode is None:
    st.html('<p class="input-label">Choose input</p>')

    tabular_col, bruker_col = st.columns(2, gap="medium")

    with tabular_col:
        with st.container(border=True):
            st.subheader("Tabular data")

            st.write(
                "Calculate MetSCORE from one or multiple samples "
                "provided as a CSV or Excel table."
            )

            st.caption("CSV / Excel · Single or multiple samples")

            st.button(
                "Use tabular data",
                type="primary",
                width="stretch",
                key="tabular_button",
                on_click=set_input_mode,
                args=("tabular",),
            )

    with bruker_col:
        with st.container(border=True):
            st.subheader("Bruker XML")

            st.write(
                "Calculate MetSCORE directly from paired metabolite "
                "and lipoprotein Bruker XML reports."
            )

            st.caption("Two XML reports · Single sample")

            st.button(
                "Use Bruker XML",
                width="stretch",
                key="bruker_button",
                on_click=set_input_mode,
                args=("bruker",),
            )

elif st.session_state.input_mode == "tabular":
    render_tabular_workflow()

elif st.session_state.input_mode == "bruker":
    render_bruker_workflow()

st.caption(
    "MetSCORE is intended for research use. "
    "The web interface uses the validated MetSCORE Python implementation."
)
