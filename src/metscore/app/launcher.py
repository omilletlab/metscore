from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Launch the MetSCORE Streamlit interface."""
    if importlib.util.find_spec("streamlit") is None:
        print(
            "MetSCORE GUI dependencies are not installed. "
            'Install MetSCORE with the "app" optional dependency.',
            file=sys.stderr,
        )
        return 2

    app_path = Path(__file__).with_name("streamlit_app.py")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
        ],
        check=False,
    )

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
