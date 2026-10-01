"""Start the single-process Flask application with ``python app.py``."""

import os

from backend import create_app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
