import json
import sqlite3
import sys
import tempfile
import zipfile

try:
    import zstandard
except ImportError:
    sys.exit("Missing dependency: zstandard\n  pip install zstandard")


def get_lapis_model_id(apkg_path: str) -> int:
    """Read an .apkg and return the model ID for the 'Lapis' note type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(apkg_path) as zf:
            names = zf.namelist()

            if "collection.anki21b" in names:
                zf.extract("collection.anki21b", tmpdir)
                compressed = f"{tmpdir}/collection.anki21b"
                db_path = f"{tmpdir}/collection.db"
                with open(compressed, "rb") as src, open(db_path, "wb") as dst:
                    zstandard.ZstdDecompressor().copy_stream(src, dst)
            elif "collection.anki21" in names:
                zf.extract("collection.anki21", tmpdir)
                db_path = f"{tmpdir}/collection.anki21"
            else:
                zf.extract("collection.anki2", tmpdir)
                db_path = f"{tmpdir}/collection.anki2"

        con = sqlite3.connect(db_path)
        con.create_collation("unicase", lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
        try:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "notetypes" in tables:
                row = con.execute("SELECT id FROM notetypes WHERE name = 'Lapis'").fetchone()
                if row:
                    return int(row[0])
            else:
                row = con.execute("SELECT models FROM col").fetchone()
                if row:
                    for model_id, model in json.loads(row[0]).items():
                        if model.get("name") == "Lapis":
                            return int(model_id)
        finally:
            con.close()

    raise ValueError("Lapis note type not found in the collection")


def list_decks(collection_path: str) -> list[dict[str, object]]:
    """List all decks in a live Anki collection.

    `collection_path` accepts:
    - An Anki profile directory (e.g. .../Anki2/User 1/) — auto-detects the collection file.
    - A direct path to collection.anki2 / collection.anki21 / collection.anki21b.

    Returns a list of {"id": int, "name": str} dicts sorted by deck name.

    Close Anki before calling this to avoid database lock errors.
    """
    import os
    from pathlib import Path

    path = Path(collection_path)
    if path.is_dir():
        for candidate in ("collection.anki21b", "collection.anki21", "collection.anki2"):
            p = path / candidate
            if p.exists():
                path = p
                break
        else:
            raise FileNotFoundError(f"No collection file found in: {collection_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        if path.suffix == ".anki21b":
            db_path = os.path.join(tmpdir, "collection.db")
            with open(path, "rb") as src, open(db_path, "wb") as dst:
                zstandard.ZstdDecompressor().copy_stream(src, dst)
        else:
            db_path = str(path)

        con = sqlite3.connect(db_path)
        con.create_collation("unicase", lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
        try:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "decks" in tables:
                # Anki schema >= 15 (anki21 / anki21b): dedicated decks table
                rows = con.execute("SELECT id, name FROM decks").fetchall()
                decks = [{"id": int(r[0]), "name": r[1]} for r in rows]
            else:
                # Legacy schema (anki2): decks stored as JSON blob in col.decks
                row = con.execute("SELECT decks FROM col").fetchone()
                decks = (
                    [{"id": int(d["id"]), "name": d["name"]} for d in json.loads(row[0]).values()]
                    if row else []
                )
        finally:
            con.close()

    return sorted(decks, key=lambda d: d["name"])
