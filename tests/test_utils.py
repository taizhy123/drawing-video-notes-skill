from pathlib import Path

from art_course_notes.utils import format_timestamp, safe_stem


def test_timestamp_formats_and_clamps_negative_values():
    assert format_timestamp(0) == "00:00:00"
    assert format_timestamp(3723.456, milliseconds=True) == "01:02:03.456"
    assert format_timestamp(-4) == "00:00:00"


def test_safe_stem_supports_windows_unsafe_names():
    assert safe_stem(Path("D:/课程/01:色彩?基础.mp4")) == "01_色彩_基础"
