from art_course_notes.chunking import create_chunks
from art_course_notes.models import Segment


def test_chunks_follow_speech_boundaries_and_keep_transcript_overlap():
    segments = [Segment(start, start + 20, "讲解") for start in range(0, 1800, 60)]
    chunks = create_chunks(segments, duration=1800, target_minutes=10, min_minutes=8, max_minutes=12, overlap_seconds=30)
    assert len(chunks) == 3
    assert chunks[0].start == 0
    assert chunks[-1].end == 1800
    assert chunks[0].end == chunks[1].start
    assert chunks[1].transcript_start == chunks[1].start - 30
    assert all(480 <= chunk.end - chunk.start <= 720 for chunk in chunks[:-1])
