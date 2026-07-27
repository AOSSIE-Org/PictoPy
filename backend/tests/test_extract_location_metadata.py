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


LATITUDE_LIMIT = 90.0
LONGITUDE_LIMIT = 180.0


def resolve_latitude(*candidates):
    """Resolve a latitude from candidates in order of preference."""
    return MetadataExtractor._resolve_coordinate("latitude", candidates, LATITUDE_LIMIT)


class TestResolveCoordinate:
    """Test class for the per-candidate resolver behind the fallback chain."""

    def test_zero_is_kept(self):
        """0 and 0.0 are real coordinates, not missing values."""
        assert resolve_latitude(0) == 0.0
        assert resolve_latitude(0.0) == 0.0

    def test_none_is_skipped(self):
        """None falls through to the next candidate."""
        assert resolve_latitude(None, 28.6) == 28.6

    @pytest.mark.parametrize("blank", ["", "   ", "\t"])
    def test_blank_string_is_skipped(self, blank):
        """Blank strings fall through to the next candidate."""
        assert resolve_latitude(blank, 28.6) == 28.6

    def test_first_usable_candidate_wins(self):
        """The earliest usable candidate takes precedence."""
        assert resolve_latitude(28.6, 45.0) == 28.6

    def test_unreadable_candidate_is_skipped(self):
        """A value that cannot become a float falls through."""
        assert resolve_latitude("not-a-number", 28.6) == 28.6

    def test_out_of_range_candidate_is_skipped(self):
        """A value outside the valid range falls through."""
        assert resolve_latitude(200, 28.6) == 28.6

    def test_numeric_strings_are_converted(self):
        """Coordinates arriving as strings are converted."""
        assert resolve_latitude("28.6") == 28.6

    def test_limits_are_inclusive(self):
        """The exact range boundaries are accepted."""
        assert resolve_latitude(90) == 90.0
        assert resolve_latitude(-90) == -90.0

    @pytest.mark.parametrize("value", ["nan", "inf", "-inf", float("nan")])
    def test_non_finite_values_are_skipped(self, value):
        """NaN and infinity are not usable coordinates."""
        assert resolve_latitude(value, 28.6) == 28.6

    @pytest.mark.parametrize("value", [[1, 2], {"a": 1}, object()])
    def test_unconvertible_types_are_skipped(self, value):
        """Values of the wrong type fall through instead of raising."""
        assert resolve_latitude(value, 28.6) == 28.6

    @pytest.mark.parametrize("value", [True, False])
    def test_booleans_are_skipped(self, value):
        """bool is a subclass of int, but it is not a coordinate."""
        assert resolve_latitude(value, 28.6) == 28.6

    def test_returns_none_when_no_candidate_qualifies(self):
        """None is returned when every candidate is unusable."""
        assert resolve_latitude(None, "", "junk", 200) is None
        assert resolve_latitude() is None

    def test_longitude_range_is_wider_than_latitude(self):
        """120 is a valid longitude but not a valid latitude."""
        assert (
            MetadataExtractor._resolve_coordinate("longitude", (120,), LONGITUDE_LIMIT)
            == 120.0
        )
        assert resolve_latitude(120) is None


class TestFallthroughToLowerPrioritySource:
    """
    Test class for falling through unusable values in a preferred field.

    A malformed or out-of-range coordinate in a higher-priority field must not
    mask a valid coordinate in a lower-priority one.
    """

    @pytest.mark.parametrize("bad", ["not-a-number", 200, -200, "", None, "nan"])
    def test_bad_top_level_latitude_falls_back_to_exif(self, extractor, bad):
        """An unusable top-level latitude falls through to exif.gps."""
        metadata = {
            "latitude": bad,
            "longitude": 77.2,
            "exif": {"gps": {"latitude": 28.6}},
        }
        assert extractor.extract_gps_coordinates(metadata) == (28.6, 77.2)

    @pytest.mark.parametrize("bad", ["not-a-number", 400, -400, "", None])
    def test_bad_top_level_longitude_falls_back_to_exif(self, extractor, bad):
        """An unusable top-level longitude falls through to exif.gps."""
        metadata = {
            "latitude": 28.6,
            "longitude": bad,
            "exif": {"gps": {"longitude": 77.2}},
        }
        assert extractor.extract_gps_coordinates(metadata) == (28.6, 77.2)

    def test_bad_top_level_falls_back_to_alias(self, extractor):
        """An unusable top-level value falls through to the lat/lon aliases."""
        metadata = {
            "latitude": "junk",
            "longitude": 999,
            "lat": 28.6,
            "lon": 77.2,
        }
        assert extractor.extract_gps_coordinates(metadata) == (28.6, 77.2)

    def test_falls_through_two_bad_sources_to_the_third(self, extractor):
        """Resolution continues past more than one unusable source."""
        metadata = {
            "latitude": "junk",
            "longitude": "junk",
            "exif": {"gps": {"latitude": 200, "longitude": 400}},
            "lat": 28.6,
            "lon": 77.2,
        }
        assert extractor.extract_gps_coordinates(metadata) == (28.6, 77.2)

    def test_falls_back_to_a_zero_coordinate(self, extractor):
        """Falling through still preserves a valid 0 further down the chain."""
        metadata = {
            "latitude": "junk",
            "longitude": "junk",
            "exif": {"gps": {"latitude": 0.0, "longitude": 0.0}},
        }
        assert extractor.extract_gps_coordinates(metadata) == (0.0, 0.0)

    def test_each_coordinate_falls_through_independently(self, extractor):
        """Latitude and longitude may end up resolved from different sources."""
        metadata = {
            "latitude": 28.6,
            "longitude": "junk",
            "exif": {"gps": {"longitude": 77.2}},
        }
        assert extractor.extract_gps_coordinates(metadata) == (28.6, 77.2)

    def test_no_usable_fallback_returns_none(self, extractor):
        """(None, None) is returned when no source holds a usable value."""
        metadata = {
            "latitude": "junk",
            "longitude": 999,
            "exif": {"gps": {"latitude": 200, "longitude": "also-junk"}},
        }
        assert extractor.extract_gps_coordinates(metadata) == (None, None)

    def test_unusable_latitude_with_valid_longitude_returns_none(self, extractor):
        """A resolvable longitude alone is not a location."""
        metadata = {"latitude": "junk", "longitude": 77.2}
        assert extractor.extract_gps_coordinates(metadata) == (None, None)


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
