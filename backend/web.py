"""Flask routes that connect the frontend to the business logic."""

from pathlib import Path
import sqlite3

from flask import Flask, abort, redirect, render_template, request, url_for

from database import database_path, initialize_database

from .restaurant_domain import (
    add_restaurant,
    get_restaurant_details,
    list_all_restaurants,
    list_saved_restaurants,
    remove_restaurant,
    save_existing_restaurant,
)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app():
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
    )
    app.config["DATABASE_PATH"] = database_path()
    initialize_database(app.config["DATABASE_PATH"])

    @app.get("/")
    def home():
        return render_template(
            "index.html",
            restaurants=list_saved_restaurants(app.config["DATABASE_PATH"]),
            values={},
            added=request.args.get("added"),
            removed=request.args.get("removed"),
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
                restaurants=list_saved_restaurants(app.config["DATABASE_PATH"]),
                values=values,
                added=None,
                removed=None,
                error=str(error),
            ), 400

        return redirect(url_for("home", added=restaurant_id))

    @app.get("/restaurants")
    def all_restaurants():
        return render_template(
            "all_restaurants.html",
            restaurants=list_all_restaurants(app.config["DATABASE_PATH"]),
            saved=request.args.get("saved"),
            error=None,
        )

    @app.get("/restaurants/<int:restaurant_id>")
    def restaurant_details(restaurant_id):
        restaurant = get_restaurant_details(app.config["DATABASE_PATH"], restaurant_id)
        if restaurant is None:
            abort(404, description="Restaurant not found.")
        return render_template("restaurant_details.html", restaurant=restaurant)

    @app.post("/restaurants/<int:restaurant_id>/save")
    def save_restaurant(restaurant_id):
        try:
            save_existing_restaurant(
                app.config["DATABASE_PATH"],
                restaurant_id,
                status=request.form.get("status"),
            )
        except ValueError as error:
            message, status_code = str(error), 400
        except sqlite3.IntegrityError as error:
            if "UNIQUE constraint failed" in str(error):
                message, status_code = "This restaurant is already saved.", 409
            else:
                abort(404, description="Restaurant not found.")
        else:
            return redirect(url_for("all_restaurants", saved=restaurant_id))

        return render_template(
            "all_restaurants.html",
            restaurants=list_all_restaurants(app.config["DATABASE_PATH"]),
            saved=None,
            error=message,
        ), status_code

    @app.post("/saved-restaurants/<int:saved_id>/remove")
    def remove_saved_restaurant(saved_id):
        try:
            remove_restaurant(app.config["DATABASE_PATH"], saved_id)
        except ValueError as error:
            abort(404, description=str(error))
        return redirect(url_for("home", removed=1))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
