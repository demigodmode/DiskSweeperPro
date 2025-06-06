from pathlib import Path
from sweeper.core.collector import _walk_size

def test_walk_size(tmp_path: Path):
    f = tmp_path / "dummy.bin"
    f.write_bytes(b"x" * 1234)
    assert _walk_size(tmp_path, cutoff=None) == 1234
