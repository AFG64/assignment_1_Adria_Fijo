"""Flask routes that connect the frontend to the business logic."""

from datetime import date
import math
from pathlib import Path
import sqlite3

from flask import Flask, abort, redirect, render_template, request, send_file, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from database import database_path, initialize_database

from .bill_files import MAX_BILL_BYTES, remove_bill_file, store_bill_file, stored_bill_path
from .dining_history import add_bill, add_visit, get_bill_path, get_visit, list_bill_paths, list_visits
from .geocoding import geocode_address, search_query
from .restaurant_domain import (
    add_restaurant,
    get_restaurant_details,
    list_all_restaurants,
    list_saved_restaurants,
    remove_restaurant,
    save_existing_restaurant,
    update_restaurant_location,
)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app():
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
    )
    app.config["DATABASE_PATH"] = database_path()
    app.config["MAX_CONTENT_LENGTH"] = MAX_BILL_BYTES + 1024 * 1024
    initialize_database(app.config["DATABASE_PATH"])

    def render_restaurant_details(restaurant_id, **context):
        restaurant = get_restaurant_details(app.config["DATABASE_PATH"], restaurant_id)
        if restaurant is None:
            abort(404, description="Restaurant not found.")
        visits = (
            list_visits(app.config["DATABASE_PATH"], restaurant["saved_id"])
            if restaurant["saved_id"] is not None else []
        )
        return render_template(
            "restaurant_details.html",
            restaurant=restaurant,
            visits=visits,
            today=date.today().isoformat(),
            visit_values=context.get("visit_values", {}),
            visit_error=context.get("visit_error"),
            bill_error=context.get("bill_error"),
            bill_error_visit_id=context.get("bill_error_visit_id"),
            location_error=context.get("location_error"),
            location_values=context.get("location_values", {}),
            location_saved=request.args.get("location_saved"),
            visit_added=request.args.get("visit_added"),
            bill_added=request.args.get("bill_added"),
        )

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
            if not (values.get("title") or "").strip():
                raise ValueError("Restaurant name is required.")
            address = (values.get("address") or "").strip()
            if len(address) > 300:
                raise ValueError("Location must be 300 characters or fewer.")
            coordinates = (
                geocode_address(
                    app.config["DATABASE_PATH"],
                    search_query(address, values.get("city")),
                ) if address else None
            )
            restaurant_id = add_restaurant(
                app.config["DATABASE_PATH"],
                title=values.get("title"),
                category_name=values.get("category_name"),
                city=values.get("city"),
                price=values.get("price"),
                rating=values.get("rating"),
                notes=values.get("notes"),
                status=values.get("status", "want_to_go"),
                address=address or None,
                latitude=coordinates["latitude"] if coordinates else None,
                longitude=coordinates["longitude"] if coordinates else None,
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
        return render_restaurant_details(restaurant_id)

    @app.post("/restaurants/<int:restaurant_id>/location")
    def save_restaurant_location(restaurant_id):
        restaurant = get_restaurant_details(app.config["DATABASE_PATH"], restaurant_id)
        if restaurant is None:
            abort(404, description="Restaurant not found.")
        values = request.form.to_dict()
        address = (values.get("address") or "").strip()
        try:
            if len(address) > 300:
                raise ValueError("Location must be 300 characters or fewer.")
            coordinates = geocode_address(
                app.config["DATABASE_PATH"],
                search_query(address, restaurant["city"]),
            )
            update_restaurant_location(
                app.config["DATABASE_PATH"], restaurant_id, address,
                coordinates["latitude"], coordinates["longitude"],
            )
        except ValueError as error:
            return render_restaurant_details(
                restaurant_id, location_error=str(error), location_values=values,
            ), 400
        return redirect(url_for("restaurant_details", restaurant_id=restaurant_id, location_saved=1) + "#location")

    @app.post("/restaurants/<int:restaurant_id>/visits")
    def create_visit(restaurant_id):
        restaurant = get_restaurant_details(app.config["DATABASE_PATH"], restaurant_id)
        if restaurant is None or restaurant["saved_id"] is None:
            abort(404, description="Save this restaurant before recording a visit.")

        values = request.form.to_dict()
        try:
            try:
                visit_date = date.fromisoformat(values.get("visit_date", ""))
            except (TypeError, ValueError) as error:
                raise ValueError("Enter a valid visit date.") from error
            if visit_date > date.today():
                raise ValueError("Visit date cannot be in the future.")
            rating_text = values.get("rating", "").strip()
            try:
                rating = float(rating_text) if rating_text else None
            except ValueError as error:
                raise ValueError("Visit rating must be from 0 to 5.") from error
            if rating is not None and (not math.isfinite(rating) or not 0 <= rating <= 5):
                raise ValueError("Visit rating must be from 0 to 5.")
            notes = values.get("notes", "").strip() or None
            if notes is not None and len(notes) > 2000:
                raise ValueError("Visit notes must be 2000 characters or fewer.")
            visit_id = add_visit(
                app.config["DATABASE_PATH"], restaurant["saved_id"],
                visit_date.isoformat(), rating, notes,
            )
        except ValueError as error:
            return render_restaurant_details(
                restaurant_id, visit_error=str(error), visit_values=values,
            ), 400
        except sqlite3.IntegrityError:
            abort(404, description="Saved restaurant not found.")

        return redirect(url_for("restaurant_details", restaurant_id=restaurant_id, visit_added=visit_id) + "#visits")

    @app.post("/restaurants/<int:restaurant_id>/visits/<int:visit_id>/bills")
    def upload_bill(restaurant_id, visit_id):
        restaurant = get_restaurant_details(app.config["DATABASE_PATH"], restaurant_id)
        if (restaurant is None or restaurant["saved_id"] is None
                or get_visit(app.config["DATABASE_PATH"], restaurant["saved_id"], visit_id) is None):
            abort(404, description="Visit not found for this restaurant.")

        image_path = None
        try:
            image_path = store_bill_file(
                app.config["DATABASE_PATH"], request.files.get("bill_file"),
            )
            add_bill(app.config["DATABASE_PATH"], visit_id, image_path)
        except RequestEntityTooLarge:
            return render_restaurant_details(
                restaurant_id, bill_error="The bill file must be 5 MB or smaller.",
                bill_error_visit_id=visit_id,
            ), 413
        except ValueError as error:
            if image_path:
                remove_bill_file(app.config["DATABASE_PATH"], image_path)
            return render_restaurant_details(
                restaurant_id, bill_error=str(error), bill_error_visit_id=visit_id,
            ), 400
        except sqlite3.IntegrityError:
            if image_path:
                remove_bill_file(app.config["DATABASE_PATH"], image_path)
            abort(404, description="Visit no longer exists.")
        except Exception:
            if image_path:
                remove_bill_file(app.config["DATABASE_PATH"], image_path)
            raise

        return redirect(url_for("restaurant_details", restaurant_id=restaurant_id, bill_added=visit_id) + f"#visit-{visit_id}")

    @app.get("/restaurants/<int:restaurant_id>/visits/<int:visit_id>/bills/<int:bill_id>")
    def download_bill(restaurant_id, visit_id, bill_id):
        restaurant = get_restaurant_details(app.config["DATABASE_PATH"], restaurant_id)
        if restaurant is None or restaurant["saved_id"] is None:
            abort(404)
        image_path = get_bill_path(
            app.config["DATABASE_PATH"], restaurant["saved_id"], visit_id, bill_id,
        )
        if image_path is None:
            abort(404)
        try:
            file_path = stored_bill_path(app.config["DATABASE_PATH"], image_path)
        except ValueError:
            abort(404)
        if not file_path.is_file():
            abort(404)
        return send_file(file_path, as_attachment=True, download_name=f"bill-{bill_id}{file_path.suffix}")

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
            bill_paths = list_bill_paths(app.config["DATABASE_PATH"], saved_id)
            remove_restaurant(app.config["DATABASE_PATH"], saved_id)
        except ValueError as error:
            abort(404, description=str(error))
        for image_path in bill_paths:
            remove_bill_file(app.config["DATABASE_PATH"], image_path)
        return redirect(url_for("home", removed=1))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
