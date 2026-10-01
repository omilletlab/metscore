from io import BytesIO
from pathlib import Path

import streamlit as st


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
