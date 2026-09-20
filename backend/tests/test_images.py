import pytest
from app.utils.images import _convert_to_degrees, _extract_gps_coordinates

class MockFraction:
    def __init__(self, num, den):
        self.numerator = num
        self.denominator = den

class MockExifData:
    def __init__(self, gps_data):
        self.gps_data = gps_data

    def get_ifd(self, tag):
        # 34853 is GPS_INFO_TAG
        if tag == 34853:
            return self.gps_data
        return None

def test_convert_to_degrees_zero_denominator():
    """Test that a zero denominator correctly raises a ValueError."""
    bad_value = (MockFraction(10, 0), MockFraction(20, 1), MockFraction(30, 1))
    with pytest.raises(ValueError, match="Denominator cannot be zero"):
        _convert_to_degrees(bad_value)

def test_extract_gps_coordinates_zero_denominator_handled():
    """Test that a corrupted GPS tag with zero denominator does not crash the extraction."""
    mock_gps_data = {
        1: "N",
        2: (MockFraction(10, 0), MockFraction(20, 1), MockFraction(30, 1)),
        3: "E",
        4: (MockFraction(10, 1), MockFraction(20, 1), MockFraction(30, 1))
    }
    mock_exif = MockExifData(mock_gps_data)
    
    # This should not raise an exception, but return (None, None)
    lat, lon = _extract_gps_coordinates(mock_exif)
    
    assert lat is None
    assert lon is None
