from pathlib import Path

import streamlit as st

from bruker_workflow import render_bruker_workflow
from tabular_workflow import render_tabular_workflow

APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "assets" / "omilletlab-logo.png"


def set_input_mode(mode: str) -> None:
    st.session_state.input_mode = mode


def initialize_session_state() -> None:
    if "input_mode" not in st.session_state:
        st.session_state.input_mode = None

    if "selected_result_row" not in st.session_state:
        st.session_state.selected_result_row = None

    if "tabular_uploader_version" not in st.session_state:
        st.session_state.tabular_uploader_version = 0

    if "bruker_uploader_version" not in st.session_state:
        st.session_state.bruker_uploader_version = 0


def render_styles() -> None:
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


def render_header() -> None:
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
                <a
                    href="https://github.com/omilletlab/metscore"
                    target="_blank"
                >
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


def render_input_selector() -> None:
    st.html('<p class="input-label">Choose input</p>')

    tabular_col, bruker_col = st.columns(
        2,
        gap="medium",
    )

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
                type="primary",
                width="stretch",
                key="bruker_button",
                on_click=set_input_mode,
                args=("bruker",),
            )


def render_footer() -> None:
    st.caption(
        "MetSCORE is intended for research use. "
        "The web interface uses the validated MetSCORE Python implementation."
    )


def main() -> None:
    st.set_page_config(
        page_title="MetSCORE",
        layout="wide",
    )

    initialize_session_state()
    render_styles()
    render_header()

    if st.session_state.input_mode is None:
        render_input_selector()

    elif st.session_state.input_mode == "tabular":
        render_tabular_workflow()

    elif st.session_state.input_mode == "bruker":
        render_bruker_workflow()

    render_footer()


if __name__ == "__main__":
    main()
