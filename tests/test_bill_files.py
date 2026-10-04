"""Uploaded bills stay in managed storage and can be retrieved safely."""

from contextlib import closing
from io import BytesIO
import sqlite3

import pytest
from werkzeug.datastructures import FileStorage

from backend.bill_files import (
    MAX_BILL_BYTES,
    remove_bill_file,
    store_bill_file,
    stored_bill_path,
)
from backend.dining_history import add_visit
from backend.restaurant_domain import add_restaurant, list_saved_restaurants
from backend.web import create_app


def upload(contents, filename="receipt.pdf"):
    return FileStorage(stream=BytesIO(contents), filename=filename)


@pytest.mark.parametrize(
    ("contents", "suffix"),
    [
        (b"%PDF-1.4\nreceipt", ".pdf"),
        (b"\x89PNG\r\n\x1a\nreceipt", ".png"),
        (b"\xff\xd8\xffreceipt", ".jpg"),
    ],
)
def test_store_and_remove_bill(tmp_path, contents, suffix):
    database_file = tmp_path / "journal.sqlite3"
    relative = store_bill_file(database_file, upload(contents, "wrong.txt"))
    stored = stored_bill_path(database_file, relative)

    assert relative.startswith("bills/") and relative.endswith(suffix)
    assert stored.parent == tmp_path / "bills"
    assert stored.read_bytes() == contents
    remove_bill_file(database_file, relative)
    assert not stored.exists()
    remove_bill_file(database_file, relative)  # Removing a missing file is safe.


@pytest.mark.parametrize(
    "file",
    [None, upload(b"%PDF-1.4", ""), upload(b"", "empty.pdf"),
     upload(b"not a bill", "fake.pdf"),
     upload(b"%PDF-" + b"x" * MAX_BILL_BYTES, "large.pdf")],
)
def test_invalid_upload_creates_no_file(tmp_path, file):
    database_file = tmp_path / "journal.sqlite3"
    with pytest.raises(ValueError):
        store_bill_file(database_file, file)
    assert not (tmp_path / "bills").exists()


@pytest.mark.parametrize(
    "path",
    ["../outside.pdf", "bills/../outside.pdf", "/tmp/outside.pdf",
     "bills/not-a-generated-name.pdf", "bills/" + "a" * 32 + ".txt"],
)
def test_only_managed_paths_can_be_resolved(tmp_path, path):
    database_file = tmp_path / "journal.sqlite3"
    with pytest.raises(ValueError):
        stored_bill_path(database_file, path)
    remove_bill_file(database_file, path)


def test_managed_name_cannot_follow_symlink_outside_bills(tmp_path):
    database_file = tmp_path / "journal.sqlite3"
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"private")
    bill_dir = tmp_path / "bills"
    bill_dir.mkdir()
    relative = "bills/" + "a" * 32 + ".pdf"
    (bill_dir / ("a" * 32 + ".pdf")).symlink_to(outside)

    with pytest.raises(ValueError):
        stored_bill_path(database_file, relative)
    remove_bill_file(database_file, relative)
    assert outside.read_bytes() == b"private"


def test_bill_upload_download_and_removal_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app()
    app.config.update(TESTING=True)
    database_file = app.config["DATABASE_PATH"]
    restaurant_id = add_restaurant(database_file, "Corner Cafe")
    saved_id = list_saved_restaurants(database_file)[0]["saved_id"]
    visit_id = add_visit(database_file, saved_id, "2026-10-01")
    client = app.test_client()

    response = client.post(
        f"/restaurants/{restaurant_id}/visits/{visit_id}/bills",
        data={"bill_file": (BytesIO(b"%PDF-1.4\nreceipt"), "receipt.pdf")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Bill attached to your visit" in response.data
    with closing(sqlite3.connect(database_file)) as connection:
        bill_id, relative = connection.execute("SELECT id, image_path FROM bills").fetchone()
    assert stored_bill_path(database_file, relative).is_file()

    download = client.get(
        f"/restaurants/{restaurant_id}/visits/{visit_id}/bills/{bill_id}"
    )
    assert download.status_code == 200
    assert download.data == b"%PDF-1.4\nreceipt"
    assert "attachment" in download.headers["Content-Disposition"]

    client.post(f"/saved-restaurants/{saved_id}/remove")
    assert not stored_bill_path(database_file, relative).exists()
