"""next_copy_path: a new numbered copy is returned, existing files are never reused."""
import tempfile
from pathlib import Path
from cv_model import next_copy_path, save_cv

with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    src = d / "my_tr.json"
    src.write_text("{}", encoding="utf-8")
    p1 = next_copy_path(src)
    assert p1.name == "my_tr_1.json", p1
    save_cv(p1, {"name": "a"})
    p2 = next_copy_path(src)
    assert p2.name == "my_tr_2.json", p2
    save_cv(p2, {"name": "b"})
    # saving from an already numbered copy must not stack suffixes
    assert next_copy_path(p2).name == "my_tr_3.json", next_copy_path(p2)
    # the original and earlier copies are untouched
    assert src.read_text(encoding="utf-8") == "{}"
    assert "a" in p1.read_text(encoding="utf-8")
    # gap: deleting _1 makes it the next free name
    p1.unlink()
    assert next_copy_path(src).name == "my_tr_1.json"
print("next_copy_path OK")
