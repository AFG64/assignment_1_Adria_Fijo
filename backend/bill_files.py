"""Store uploaded bill files outside the public static directory."""

from pathlib import Path
from uuid import uuid4


MAX_BILL_BYTES = 5 * 1024 * 1024


def _bill_suffix(contents):
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if contents.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if contents.startswith(b"%PDF-"):
        return ".pdf"
    raise ValueError("Upload a PNG, JPEG, or PDF bill.")


def store_bill_file(database_path, upload):
    """Validate an upload and return its path relative to DATA_DIR."""
    if upload is None or not upload.filename:
        raise ValueError("Choose a bill file to upload.")

    contents = upload.stream.read(MAX_BILL_BYTES + 1)
    if not contents:
        raise ValueError("The bill file is empty.")
    if len(contents) > MAX_BILL_BYTES:
        raise ValueError("The bill file must be 5 MB or smaller.")
    suffix = _bill_suffix(contents)

    bill_dir = Path(database_path).parent / "bills"
    bill_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{suffix}"
    (bill_dir / filename).write_bytes(contents)
    return f"bills/{filename}"


def stored_bill_path(database_path, image_path):
    """Resolve only filenames created in DATA_DIR/bills."""
    relative = Path(image_path)
    if (len(relative.parts) != 2 or relative.parts[0] != "bills"
            or len(relative.stem) != 32 or not all(c in "0123456789abcdef" for c in relative.stem)
            or relative.suffix not in {".png", ".jpg", ".pdf"}):
        raise ValueError("Invalid bill file path.")
    bill_dir = (Path(database_path).parent / "bills").resolve()
    file_path = (bill_dir / relative.name).resolve()
    if file_path.parent != bill_dir:
        raise ValueError("Invalid bill file path.")
    return file_path


def remove_bill_file(database_path, image_path):
    """Remove a managed bill file if it still exists."""
    try:
        stored_bill_path(database_path, image_path).unlink(missing_ok=True)
    except ValueError:
        pass
