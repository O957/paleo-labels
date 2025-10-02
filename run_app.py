"""Launch script for paleo-labels Streamlit app."""

import sys
from pathlib import Path

# add paleo_labels to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    from paleo_labels.ui.streamlit_app import main

    main()
