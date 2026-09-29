"""Single-process entry point for DevOps Food."""

import os

from flask import Flask, render_template

from storage import database_path, initialize_database


def create_app():
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = database_path()
    initialize_database(app.config["DATABASE_PATH"])

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
