import json

import pytest

from app.utils.extract_location_metadata import MetadataExtractor


@pytest.fixture
def extractor():
    """A MetadataExtractor instance."""
    return MetadataExtractor()


# ##############################
# Test Classes
# ##############################


class TestFirstPresent:
    """Test class for the presence helper that backs the fallback chain."""

    def test_zero_is_present(self):
        """0 and 0.0 are real values, not missing ones."""
        assert MetadataExtractor._first_present(0) == 0
        assert MetadataExtractor._first_present(0.0) == 0.0

    def test_none_is_skipped(self):
        """None falls through to the next candidate."""
        assert MetadataExtractor._first_present(None, 28.6) == 28.6

    def test_blank_string_is_skipped(self):
        """Empty and whitespace-only strings fall through to the next candidate."""
        assert MetadataExtractor._first_present("", 28.6) == 28.6
        assert MetadataExtractor._first_present("   ", 28.6) == 28.6

    def test_first_wins(self):
        """The earliest present candidate takes precedence."""
        assert MetadataExtractor._first_present(28.6, 77.2) == 28.6

    def test_all_absent_returns_none(self):
        """None is returned when every candidate is absent."""
        assert MetadataExtractor._first_present(None, "", None) is None
        assert MetadataExtractor._first_present() is None


class TestExtractGPSCoordinatesZeroValues:
    """Test class for coordinates on the equator and the prime meridian."""

    @pytest.mark.parametrize(
        "metadata, expected",
        [
            # Equator: latitude is exactly 0
            ({"latitude": 0.0, "longitude": 77.2}, (0.0, 77.2)),
            # Prime meridian: longitude is exactly 0
            ({"latitude": 51.5, "longitude": 0.0}, (51.5, 0.0)),
            # Null Island: both are 0
            ({"latitude": 0.0, "longitude": 0.0}, (0.0, 0.0)),
            # Integer zeros
            ({"latitude": 0, "longitude": 0}, (0.0, 0.0)),
            # Zeros as strings
            ({"latitude": "0.0", "longitude": "0.0"}, (0.0, 0.0)),
            # Negative zero
            ({"latitude": -0.0, "longitude": -0.0}, (0.0, 0.0)),
        ],
    )
    def test_zero_coordinates_are_preserved(self, extractor, metadata, expected):
        """Top-level zero coordinates survive extraction instead of being dropped."""
        assert extractor.extract_gps_coordinates(metadata) == expected

    def test_zero_in_nested_exif_gps(self, extractor):
        """Zero coordinates nested under exif.gps are preserved."""
        metadata = {"exif": {"gps": {"latitude": 0.0, "longitude": 0.0}}}
        assert extractor.extract_gps_coordinates(metadata) == (0.0, 0.0)

    @pytest.mark.parametrize(
        "metadata",
        [
            {"lat": 0.0, "lon": 0.0},
            {"Latitude": 0.0, "Longitude": 0.0},
        ],
    )
    def test_zero_in_alternative_field_names(self, extractor, metadata):
        """Zero coordinates under the lat/lon aliases are preserved."""
        assert extractor.extract_gps_coordinates(metadata) == (0.0, 0.0)

    def test_zero_mixed_with_other_source(self, extractor):
        """A zero from one source pairs correctly with a value from another."""
        metadata = {"latitude": 0.0, "exif": {"gps": {"longitude": 77.2}}}
        assert extractor.extract_gps_coordinates(metadata) == (0.0, 77.2)


class TestExtractGPSCoordinatesPrecedence:
    """Test class for which source wins when several supply the same field."""

    def test_top_level_wins_over_nested(self, extractor):
        """The top-level field takes precedence over exif.gps."""
        metadata = {
            "latitude": 28.6,
            "longitude": 77.2,
            "exif": {"gps": {"latitude": 51.5, "longitude": -0.1}},
        }
        assert extractor.extract_gps_coordinates(metadata) == (28.6, 77.2)

    def test_top_level_zero_wins_over_nested(self, extractor):
        """A top-level 0 is not overridden by a non-zero nested value."""
        metadata = {
            "latitude": 0.0,
            "longitude": 0.0,
            "exif": {"gps": {"latitude": 51.5, "longitude": -0.1}},
        }
        assert extractor.extract_gps_coordinates(metadata) == (0.0, 0.0)

    def test_nested_wins_over_aliases(self, extractor):
        """exif.gps takes precedence over the lat/lon aliases."""
        metadata = {
            "exif": {"gps": {"latitude": 51.5, "longitude": -0.1}},
            "lat": 28.6,
            "lon": 77.2,
        }
        assert extractor.extract_gps_coordinates(metadata) == (51.5, -0.1)

    def test_blank_string_falls_through_to_next_source(self, extractor):
        """A blank top-level field is treated as absent, not as a bad value."""
        metadata = {
            "latitude": "",
            "longitude": "   ",
            "exif": {"gps": {"latitude": 28.6, "longitude": 77.2}},
        }
        assert extractor.extract_gps_coordinates(metadata) == (28.6, 77.2)


class TestExtractGPSCoordinatesExisting:
    """Test class guarding the behaviour that was already correct."""

    def test_normal_coordinates(self, extractor):
        """Ordinary non-zero coordinates are extracted."""
        metadata = {"latitude": 28.6139, "longitude": 77.2090}
        assert extractor.extract_gps_coordinates(metadata) == (28.6139, 77.2090)

    def test_negative_coordinates(self, extractor):
        """Southern and western coordinates are extracted."""
        metadata = {"latitude": -33.8688, "longitude": -151.2093}
        assert extractor.extract_gps_coordinates(metadata) == (-33.8688, -151.2093)

    @pytest.mark.parametrize(
        "metadata, expected",
        [
            ({"latitude": 90, "longitude": 180}, (90.0, 180.0)),
            ({"latitude": -90, "longitude": -180}, (-90.0, -180.0)),
        ],
    )
    def test_boundary_coordinates(self, extractor, metadata, expected):
        """The extremes of the valid ranges are accepted."""
        assert extractor.extract_gps_coordinates(metadata) == expected

    @pytest.mark.parametrize(
        "metadata",
        [
            {},
            {"latitude": 28.6},  # longitude missing
            {"longitude": 77.2},  # latitude missing
            {"latitude": None, "longitude": None},
            {"other": "value"},
        ],
    )
    def test_missing_coordinates_return_none(self, extractor, metadata):
        """Absent or half-present coordinates yield (None, None)."""
        assert extractor.extract_gps_coordinates(metadata) == (None, None)

    @pytest.mark.parametrize(
        "metadata",
        [
            {"latitude": 91, "longitude": 0},
            {"latitude": -91, "longitude": 0},
            {"latitude": 0, "longitude": 181},
            {"latitude": 0, "longitude": -181},
        ],
    )
    def test_out_of_range_coordinates_rejected(self, extractor, metadata):
        """Coordinates outside the valid ranges are still rejected."""
        assert extractor.extract_gps_coordinates(metadata) == (None, None)

    def test_unparseable_coordinates_return_none(self, extractor):
        """Values that cannot become floats yield (None, None)."""
        metadata = {"latitude": "not-a-number", "longitude": "also-not"}
        assert extractor.extract_gps_coordinates(metadata) == (None, None)

    @pytest.mark.parametrize("metadata", [None, "string", 42, [1, 2]])
    def test_non_dict_metadata_returns_none(self, extractor, metadata):
        """Non-dict metadata yields (None, None) rather than raising."""
        assert extractor.extract_gps_coordinates(metadata) == (None, None)

    @pytest.mark.parametrize(
        "metadata",
        [
            {"exif": "not-a-dict"},
            {"exif": {"gps": "not-a-dict"}},
            {"exif": None},
            {"exif": {"gps": None}},
        ],
    )
    def test_malformed_exif_is_ignored(self, extractor, metadata):
        """A malformed exif/gps section is skipped without raising."""
        assert extractor.extract_gps_coordinates(metadata) == (None, None)

    def test_malformed_exif_falls_back_to_top_level(self, extractor):
        """A malformed exif section does not block the top-level fields."""
        metadata = {"latitude": 0.0, "longitude": 0.0, "exif": "not-a-dict"}
        assert extractor.extract_gps_coordinates(metadata) == (0.0, 0.0)


class TestExtractAll:
    """Test class for the JSON entry point used during image upload."""

    def test_null_island_survives_json_round_trip(self, extractor):
        """(0, 0) is preserved end to end from the metadata JSON string."""
        metadata_json = json.dumps({"latitude": 0.0, "longitude": 0.0})
        latitude, longitude, _ = extractor.extract_all(metadata_json)
        assert (latitude, longitude) == (0.0, 0.0)

    def test_equator_with_datetime(self, extractor):
        """Coordinates and datetime are extracted together."""
        metadata_json = json.dumps(
            {
                "latitude": 0.0,
                "longitude": 32.5825,
                "date_created": "2024-01-15 14:30:45",
            }
        )
        latitude, longitude, captured_at = extractor.extract_all(metadata_json)
        assert (latitude, longitude) == (0.0, 32.5825)
        assert captured_at is not None
        assert captured_at.year == 2024

    def test_bytes_metadata(self, extractor):
        """Metadata supplied as bytes is decoded before parsing."""
        metadata_json = json.dumps({"latitude": 0.0, "longitude": 0.0}).encode("utf-8")
        latitude, longitude, _ = extractor.extract_all(metadata_json)
        assert (latitude, longitude) == (0.0, 0.0)

    @pytest.mark.parametrize("metadata_json", ["", "null", None, "{not json}"])
    def test_empty_or_invalid_json(self, extractor, metadata_json):
        """Empty or unparseable metadata yields all-None without raising."""
        assert extractor.extract_all(metadata_json) == (None, None, None)
