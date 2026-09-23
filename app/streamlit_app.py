from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "assets" / "omilletlab-logo.png"


st.set_page_config(
    page_title="MetSCORE",
    layout="wide",
)

st.html(
    """
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
        padding-top: 4rem;
        padding-bottom: 3rem;
    }

    h1 {
        color: var(--text);
        font-size: clamp(3rem, 6vw, 4.5rem) !important;
        line-height: 1 !important;
        letter-spacing: -0.05em;
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
    </style>
    """
)

# Header
logo_col, identity_col, links_col = st.columns([1.25, 5.75, 2.0])

with logo_col:
    st.image(
        LOGO_PATH,
        width=120,
    )

with identity_col:
    st.markdown("**Precision Medicine & Metabolism Lab**")
    st.markdown("[CIC bioGUNE](https://www.cicbiogune.es/)")

with links_col:
    st.markdown(
        "[Lab website](https://www.omilletlab.com/) "
        "&nbsp;&nbsp;&nbsp; "
        "[GitHub](https://github.com/omilletlab/metscore)",
        unsafe_allow_html=True,
    )

st.divider()

# Introduction
st.title("MetSCORE")

st.markdown(
    "Calculate and explore a serum NMR metabolomics-based metric "
    "for metabolic syndrome."
)

st.write("")
st.markdown(
    '<p class="input-label">Choose input</p>',
    unsafe_allow_html=True,
)

# Input modes
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
            disabled=True,
            width="stretch",
            key="tabular_button",
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
            disabled=True,
            width="stretch",
            key="bruker_button",
        )

st.caption(
    "MetSCORE is intended for research use. "
    "The web interface uses the validated MetSCORE Python implementation."
)