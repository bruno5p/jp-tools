import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path


def read_apkg_fields(apkg_path: Path, field_names: list[str]) -> dict[str, list[str]]:
    """Extract specific fields from all notes in an .apkg file.

    Returns a dict mapping each field name to a list of its values across all
    notes. Notes that lack a requested field are skipped for that field only.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(apkg_path) as zf:
            names = zf.namelist()
            if "collection.anki21b" in names:
                zf.extract("collection.anki21b", tmpdir)
                compressed = Path(tmpdir) / "collection.anki21b"
                db_path = Path(tmpdir) / "collection.db"
                try:
                    import zstandard
                except ImportError:
                    raise ImportError(
                        "zstandard is required for .anki21b collections: pip install zstandard"
                    )
                with open(compressed, "rb") as src, open(db_path, "wb") as dst:
                    zstandard.ZstdDecompressor().copy_stream(src, dst)
            elif "collection.anki21" in names:
                zf.extract("collection.anki21", tmpdir)
                db_path = Path(tmpdir) / "collection.anki21"
            else:
                zf.extract("collection.anki2", tmpdir)
                db_path = Path(tmpdir) / "collection.anki2"

        con = sqlite3.connect(str(db_path))
        try:
            tables = {
                r[0]
                for r in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }

            # Build model_id → {field_name: column_index} mapping.
            # Anki schema >= 17 has a dedicated "fields" table; older versions
            # embed field metadata in the col.models JSON blob.
            model_field_map: dict[int, dict[str, int]] = {}

            if "fields" in tables:
                rows = con.execute(
                    "SELECT ntid, ord, name FROM fields ORDER BY ntid, ord"
                ).fetchall()
                for ntid, ord_, name in rows:
                    model_field_map.setdefault(int(ntid), {})[name] = int(ord_)
            else:
                row = con.execute("SELECT models FROM col").fetchone()
                if row:
                    for model_id, model in json.loads(row[0]).items():
                        model_field_map[int(model_id)] = {
                            fld["name"]: int(fld["ord"])
                            for fld in model.get("flds", [])
                        }

            result: dict[str, list[str]] = {name: [] for name in field_names}
            for mid, flds_str in con.execute("SELECT mid, flds FROM notes"):
                field_map = model_field_map.get(int(mid), {})
                flds = flds_str.split("\x1f")
                for field_name in field_names:
                    idx = field_map.get(field_name)
                    if idx is not None and idx < len(flds):
                        result[field_name].append(flds[idx])

            return result
        finally:
            con.close()
