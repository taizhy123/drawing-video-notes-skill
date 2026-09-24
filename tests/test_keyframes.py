from art_course_notes.keyframes import _distance


def test_perceptual_hash_distance_identifies_identical_hashes():
    assert _distance(0b101010, 0b101010) == 0
    assert _distance(0b101010, 0b001111) == 3
