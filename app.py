"""Single-process entry point for DevOps Food."""

import os

from flask import Flask, redirect, render_template, request, url_for

from restaurant_domain import add_restaurant, list_restaurants
from storage import database_path, initialize_database


def create_app():
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = database_path()
    initialize_database(app.config["DATABASE_PATH"])

    @app.get("/")
    def home():
        return render_template(
            "index.html",
            restaurants=list_restaurants(app.config["DATABASE_PATH"]),
            values={},
            added=request.args.get("added"),
            error=None,
        )

    @app.post("/restaurants")
    def create_restaurant():
        values = request.form.to_dict()
        try:
            restaurant_id = add_restaurant(
                app.config["DATABASE_PATH"],
                title=values.get("title"),
                category_name=values.get("category_name"),
                city=values.get("city"),
                price=values.get("price"),
                rating=values.get("rating"),
                notes=values.get("notes"),
                status=values.get("status", "want_to_go"),
            )
        except ValueError as error:
            return render_template(
                "index.html",
                restaurants=list_restaurants(app.config["DATABASE_PATH"]),
                values=values,
                added=None,
                error=str(error),
            ), 400

        return redirect(url_for("home", added=restaurant_id))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
