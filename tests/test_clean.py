from pathlib import Path
from sweeper.core.cleaner import clean
from sweeper.core.rules import Candidate, Rule

def test_clean(tmp_path: Path):
    p = tmp_path / "trash.txt"
    p.write_text("junk")
    size = p.stat().st_size
    cand = Candidate(Rule("tmp", p), p, size)
    freed = clean([cand], echo=False)
    assert freed == size and not p.exists()
