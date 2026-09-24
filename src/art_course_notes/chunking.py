from typing import Iterable, List

from .models import Chunk, Segment


def _near_boundary(segments: List[Segment], desired: float, minimum: float, maximum: float) -> float:
    candidates = [s.end for s in segments if minimum <= s.end <= maximum]
    if not candidates:
        return min(maximum, desired)
    # Prefer an actual speech boundary, weighted toward the intended duration.
    return min(candidates, key=lambda value: abs(value - desired))


def create_chunks(
    segments: Iterable[Segment],
    duration: float,
    target_minutes: float = 12,
    min_minutes: float = 8,
    max_minutes: float = 15,
    overlap_seconds: float = 30,
) -> List[Chunk]:
    """Create speech-aware chunks. Transcript ranges overlap; primary ranges do not."""
    ordered = sorted(segments, key=lambda item: (item.start, item.end))
    if duration <= 0:
        return []
    target, minimum, maximum = target_minutes * 60, min_minutes * 60, max_minutes * 60
    chunks: List[Chunk] = []
    start = 0.0
    index = 1
    while start < duration:
        if duration - start <= maximum:
            end = duration
        else:
            end = _near_boundary(ordered, start + target, start + minimum, start + maximum)
        transcript_start = max(0.0, start - (overlap_seconds if chunks else 0))
        transcript_end = min(duration, end + overlap_seconds)
        contained = [s for s in ordered if s.end >= transcript_start and s.start <= transcript_end]
        chunks.append(Chunk(
            id="chunk-%03d" % index,
            start=round(start, 3), end=round(end, 3),
            transcript_start=round(transcript_start, 3), transcript_end=round(transcript_end, 3),
            transcript=contained,
        ))
        if end <= start:
            break
        start, index = end, index + 1
    return chunks
