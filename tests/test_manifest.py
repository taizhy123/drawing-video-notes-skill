from pathlib import Path

from art_course_notes.models import Chunk, Segment
from art_course_notes.pipeline import _chunk_from_dict, _save_chunks
from art_course_notes.utils import read_json


def test_chunk_manifest_round_trip(tmp_path: Path):
    chunk = Chunk("chunk-001", 0, 120, 0, 150, [Segment(0, 4, "明暗关系")], ["assets/keyframes/chunk-001_00_00_00.jpg"])
    _save_chunks(tmp_path, [chunk])
    index = read_json(tmp_path / "chunks" / "index.json")
    restored = _chunk_from_dict(read_json(tmp_path / index[0]["path"]))
    assert restored.to_dict() == chunk.to_dict()
