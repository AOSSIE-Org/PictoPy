"""
The portable half of a photo's metadata: the XMP packet, and getting it into a
JPEG or PNG without recompressing the image.

Two things these lean on hardest. A photo may already carry XMP from another
application, and that must survive. And a face box is stored in the pixel space
OpenCV decodes, which ignores EXIF orientation, while MWG regions are defined
against the image as displayed.
"""

import io
import re
import xml.etree.ElementTree as ET

import pytest
from PIL import Image

from app.utils.xmp_packet import (
    PhotoMetadata,
    UnreadablePacketError,
    xmp_packet_applied_dimensions,
    xmp_packet_build,
    xmp_packet_orient_region,
    xmp_packet_read,
)
from app.utils.xmp_segments import (
    UnsupportedImageError,
    xmp_segments_read,
    xmp_segments_write,
)


def _jpeg(size=(64, 48), **save_kwargs) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (120, 60, 30)).save(
        buffer, "JPEG", quality=95, **save_kwargs
    )
    return buffer.getvalue()


def _png(size=(64, 48)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (30, 120, 60)).save(buffer, "PNG")
    return buffer.getvalue()


def _pixels(data: bytes):
    return list(Image.open(io.BytesIO(data)).convert("RGB").get_flattened_data())


def _scan_data(jpeg: bytes) -> bytes:
    """Everything from the start-of-scan on: the compressed image itself."""
    return jpeg[jpeg.index(b"\xff\xda") :]


def _idat(png: bytes) -> bytes:
    return png[png.index(b"IDAT") :]


SAMPLE: PhotoMetadata = {
    "keywords": ["beach", "sunset"],
    "hierarchical_keywords": ["People|Mom"],
    "rating": 5,
    "regions": [
        {
            "name": "Mom",
            "center_x": 0.25,
            "center_y": 0.4,
            "width": 0.1,
            "height": 0.2,
        }
    ],
    "applied_width": 4000,
    "applied_height": 3000,
    "written_at": "2026-08-10T12:00:00",
}


class TestPacketRoundTrip:
    def test_everything_written_reads_back(self):
        packet = xmp_packet_build(SAMPLE)
        result = xmp_packet_read(packet)

        assert result["keywords"] == ["beach", "sunset"]
        assert result["hierarchical_keywords"] == ["People|Mom"]
        assert result["rating"] == 5
        assert result["written_at"] == "2026-08-10T12:00:00"
        assert result["regions"] == SAMPLE["regions"]

    def test_an_empty_packet_is_still_valid(self):
        assert xmp_packet_read(xmp_packet_build({})) == {}

    def test_the_packet_declares_readable_prefixes(self):
        """ns0: prefixes parse, but make the packet unreadable to a human."""
        packet = xmp_packet_build(SAMPLE)
        assert b"ns0:" not in packet
        assert b"<dc:subject>" in packet
        assert b"mwg-rs:Regions" in packet

    def test_regions_use_the_normalized_area_form(self):
        packet = xmp_packet_build(SAMPLE)
        assert b'stArea:unit="normalized"' in packet
        assert b'stDim:unit="pixel"' in packet


class TestPacketMatchesTheSchema:
    """
    Read back with a plain parser, by the paths the published schemas define.

    Verifying with our own reader only proves it agrees with our writer. What
    matters is that Lightroom or digiKam finds what it goes looking for.
    """

    NS = {
        "x": "adobe:ns:meta/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "xmp": "http://ns.adobe.com/xap/1.0/",
        "mwg-rs": "http://www.metadataworkinggroup.com/schemas/regions/",
        "stArea": "http://ns.adobe.com/xmp/sType/Area#",
    }

    def _root(self):
        packet = xmp_packet_build(SAMPLE)
        body = re.search(rb"<x:xmpmeta.*</x:xmpmeta>", packet, re.S).group(0)
        return ET.fromstring(body)

    def test_keywords_sit_where_dublin_core_says(self):
        found = self._root().findall(".//dc:subject/rdf:Bag/rdf:li", self.NS)
        assert [item.text for item in found] == ["beach", "sunset"]

    def test_the_rating_sits_where_the_xmp_schema_says(self):
        assert self._root().find(".//xmp:Rating", self.NS).text == "5"

    def test_a_face_region_sits_where_mwg_says(self):
        region = self._root().find(
            ".//mwg-rs:Regions/mwg-rs:RegionList/rdf:Bag/rdf:li", self.NS
        )

        assert region.find("mwg-rs:Name", self.NS).text == "Mom"
        assert region.find("mwg-rs:Type", self.NS).text == "Face"

        area = region.find("mwg-rs:Area", self.NS)
        assert area.get(f"{{{self.NS['stArea']}}}x") == "0.25"
        assert area.get(f"{{{self.NS['stArea']}}}unit") == "normalized"


class TestPacketMerging:
    """A photo carrying Lightroom's metadata must not lose it to our write."""

    EXISTING = (
        b'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>'
        b'<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        b'<rdf:Description rdf:about="" '
        b'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        b'xmlns:xmp="http://ns.adobe.com/xap/1.0/">'
        b"<dc:creator><rdf:Seq><rdf:li>Someone Else</rdf:li></rdf:Seq></dc:creator>"
        b"<dc:rights>All rights reserved</dc:rights>"
        b"<dc:subject><rdf:Bag><rdf:li>old-tag</rdf:li></rdf:Bag></dc:subject>"
        b"<xmp:Rating>2</xmp:Rating>"
        b"</rdf:Description></rdf:RDF></x:xmpmeta>"
        b'<?xpacket end="w"?>'
    )

    def test_foreign_properties_survive(self):
        packet = xmp_packet_build(SAMPLE, existing=self.EXISTING)
        assert b"Someone Else" in packet
        assert b"All rights reserved" in packet

    def test_our_own_properties_are_replaced_not_duplicated(self):
        packet = xmp_packet_build(SAMPLE, existing=self.EXISTING)

        assert b"old-tag" not in packet
        assert packet.count(b"<dc:subject>") == 1
        assert packet.count(b"<xmp:Rating>") == 1
        assert xmp_packet_read(packet)["rating"] == 5

    def test_a_rating_held_as_an_attribute_is_also_replaced(self):
        """XMP allows either spelling, and a missed one would read as a duplicate."""
        existing = (
            b'<x:xmpmeta xmlns:x="adobe:ns:meta/">'
            b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            b'<rdf:Description rdf:about="" '
            b'xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmp:Rating="1"/>'
            b"</rdf:RDF></x:xmpmeta>"
        )
        packet = xmp_packet_build({"rating": 4}, existing=existing)

        assert xmp_packet_read(packet)["rating"] == 4
        assert b'xmp:Rating="1"' not in packet

    def test_a_bare_rdf_root_is_merged_not_discarded(self):
        """The xmpmeta wrapper is optional, and some writers leave it out."""
        existing = (
            b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            b'<rdf:Description rdf:about="" '
            b'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            b"<dc:rights>Theirs</dc:rights>"
            b"</rdf:Description></rdf:RDF>"
        )
        packet = xmp_packet_build(SAMPLE, existing=existing)

        assert b"Theirs" in packet
        assert xmp_packet_read(packet)["rating"] == 5

    def test_writing_twice_does_not_accumulate(self):
        once = xmp_packet_build(SAMPLE)
        twice = xmp_packet_build(SAMPLE, existing=once)

        assert twice.count(b"<dc:subject>") == 1
        assert xmp_packet_read(twice) == xmp_packet_read(once)


class TestPacketRefusesHostileInput:
    # Carries a real rating, so a guard that failed to fire would show up as a
    # rating being read rather than as an empty result that proves nothing.
    BOMB = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE x [<!ENTITY a "aaaaaaaaaa">'
        b'<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]>'
        b'<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        b'<rdf:Description rdf:about="" '
        b'xmlns:xmp="http://ns.adobe.com/xap/1.0/">'
        b"<xmp:Rating>3</xmp:Rating>"
        b"</rdf:Description></rdf:RDF></x:xmpmeta>"
    )

    def test_a_packet_with_a_dtd_is_not_parsed(self):
        """
        Entity expansion is the one XML attack ElementTree still allows, and the
        XMP spec forbids a DTD in a packet anyway.
        """
        assert xmp_packet_read(self.BOMB) == {}

    def test_writing_over_an_unreadable_packet_is_refused(self):
        """
        We cannot see what the file is carrying, so we cannot know what
        overwriting it would destroy. Leaving it alone is the only safe answer.
        """
        with pytest.raises(UnreadablePacketError):
            xmp_packet_build(SAMPLE, existing=self.BOMB)

    def test_writing_over_malformed_xml_is_refused(self):
        with pytest.raises(UnreadablePacketError):
            xmp_packet_build(SAMPLE, existing=b"<x:xmpmeta>truncated")

    def test_a_photo_carrying_no_packet_is_still_written(self):
        """Absent is not the same as unreadable, and must not be confused for it."""
        assert xmp_packet_read(xmp_packet_build(SAMPLE, existing=b""))["rating"] == 5

    def test_malformed_xml_reads_as_empty_rather_than_raising(self):
        """Reading is best-effort; only writing has anything to lose."""
        assert xmp_packet_read(b"<x:xmpmeta>truncated") == {}

    def test_a_non_numeric_rating_is_skipped(self):
        existing = (
            b'<x:xmpmeta xmlns:x="adobe:ns:meta/">'
            b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            b'<rdf:Description rdf:about="" '
            b'xmlns:xmp="http://ns.adobe.com/xap/1.0/">'
            b"<xmp:Rating>excellent</xmp:Rating>"
            b"</rdf:Description></rdf:RDF></x:xmpmeta>"
        )
        assert "rating" not in xmp_packet_read(existing)


class TestRegionOrientation:
    """
    A face box is recorded before EXIF rotation is applied; an MWG region is
    read after it. Getting this wrong puts every box on a rotated photo in the
    wrong place, and does it silently.
    """

    # Box in the raw top-left, taller than it is wide, so no symmetry can hide
    # a transposed axis.
    BBOX = {"x": 0, "y": 0, "width": 20, "height": 40}

    @pytest.mark.parametrize(
        "orientation,expected",
        [
            (1, (0.1, 0.2, 0.2, 0.4)),
            (2, (0.9, 0.2, 0.2, 0.4)),
            (3, (0.9, 0.8, 0.2, 0.4)),
            (4, (0.1, 0.8, 0.2, 0.4)),
            (5, (0.2, 0.1, 0.4, 0.2)),
            (6, (0.8, 0.1, 0.4, 0.2)),
            (7, (0.8, 0.9, 0.4, 0.2)),
            (8, (0.2, 0.9, 0.4, 0.2)),
        ],
    )
    def test_every_orientation_lands_where_it_should(self, orientation, expected):
        assert xmp_packet_orient_region(self.BBOX, 100, 100, orientation) == expected

    def test_the_centre_is_the_centre_not_the_corner(self):
        """MWG's x and y are the region's midpoint; a corner would offset every box."""
        centred = xmp_packet_orient_region(
            {"x": 40, "y": 40, "width": 20, "height": 20}, 100, 100, 1
        )
        assert centred == (0.5, 0.5, 0.2, 0.2)

    @pytest.mark.parametrize("orientation", [5, 6, 7, 8])
    def test_a_quarter_turn_swaps_the_applied_dimensions(self, orientation):
        assert xmp_packet_applied_dimensions(4000, 3000, orientation) == (3000, 4000)

    @pytest.mark.parametrize("orientation", [1, 2, 3, 4])
    def test_a_flip_leaves_the_applied_dimensions_alone(self, orientation):
        assert xmp_packet_applied_dimensions(4000, 3000, orientation) == (4000, 3000)

    def test_an_empty_box_has_no_region(self):
        assert (
            xmp_packet_orient_region(
                {"x": 0, "y": 0, "width": 0, "height": 10}, 100, 100
            )
            is None
        )

    def test_an_unknown_image_size_has_no_region(self):
        assert xmp_packet_orient_region(self.BBOX, 0, 0) is None

    def test_an_unrecognised_orientation_is_treated_as_upright(self):
        assert xmp_packet_orient_region(self.BBOX, 100, 100, 99) == (
            0.1,
            0.2,
            0.2,
            0.4,
        )


class TestJpegSplice:
    def test_a_packet_survives_the_round_trip(self):
        written = xmp_segments_write(_jpeg(), b"<x:xmpmeta/>")
        assert xmp_segments_read(written) == b"<x:xmpmeta/>"

    def test_a_file_without_xmp_reads_as_none(self):
        assert xmp_segments_read(_jpeg()) is None

    def test_the_image_is_not_recompressed(self):
        """The whole reason for splicing rather than decode-and-save."""
        original = _jpeg()
        written = xmp_segments_write(original, b"<x:xmpmeta/>")

        assert _pixels(original) == _pixels(written)
        assert _scan_data(written) == _scan_data(original)

    def test_rewriting_replaces_rather_than_appends(self):
        once = xmp_segments_write(_jpeg(), b"<x:xmpmeta>first</x:xmpmeta>")
        twice = xmp_segments_write(once, b"<x:xmpmeta>second</x:xmpmeta>")

        assert xmp_segments_read(twice) == b"<x:xmpmeta>second</x:xmpmeta>"
        assert twice.count(b"http://ns.adobe.com/xap/1.0/\x00") == 1
        assert b"first" not in twice

    def test_the_segment_lands_after_the_leading_app_run(self):
        """JFIF expects its APP0 first; putting ours ahead of it breaks readers."""
        written = xmp_segments_write(_jpeg(), b"<x:xmpmeta/>")
        assert written.index(b"JFIF") < written.index(b"ns.adobe.com/xap")

    def test_existing_exif_is_preserved(self):
        image = Image.new("RGB", (16, 16), "white")
        exif = image.getexif()
        exif[0x010E] = "a description"
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", exif=exif)

        written = xmp_segments_write(buffer.getvalue(), b"<x:xmpmeta/>")

        assert Image.open(io.BytesIO(written)).getexif()[0x010E] == "a description"

    def test_an_oversized_packet_is_refused(self):
        """Beyond this a packet needs ExtendedXMP; a truncated segment is corrupt."""
        with pytest.raises(ValueError, match="segment limit"):
            xmp_segments_write(_jpeg(), b"x" * 70000)

    def test_a_packet_just_under_the_limit_is_accepted(self):
        packet = b"<x:xmpmeta>" + b"y" * 65000 + b"</x:xmpmeta>"
        written = xmp_segments_write(_jpeg(), packet)
        assert xmp_segments_read(written) == packet


class TestPngSplice:
    def test_a_packet_survives_the_round_trip(self):
        written = xmp_segments_write(_png(), b"<x:xmpmeta/>")
        assert xmp_segments_read(written) == b"<x:xmpmeta/>"

    def test_a_file_without_xmp_reads_as_none(self):
        assert xmp_segments_read(_png()) is None

    def test_the_image_data_is_untouched(self):
        original = _png()
        written = xmp_segments_write(original, b"<x:xmpmeta/>")

        assert _pixels(original) == _pixels(written)
        assert _idat(written) == _idat(original)

    def test_rewriting_replaces_rather_than_appends(self):
        once = xmp_segments_write(_png(), b"<x:xmpmeta>first</x:xmpmeta>")
        twice = xmp_segments_write(once, b"<x:xmpmeta>second</x:xmpmeta>")

        assert xmp_segments_read(twice) == b"<x:xmpmeta>second</x:xmpmeta>"
        assert twice.count(b"XML:com.adobe.xmp") == 1

    def test_the_chunk_carries_a_valid_crc(self):
        """A bad CRC makes the file unreadable to a strict decoder."""
        written = xmp_segments_write(_png(), b"<x:xmpmeta/>")
        Image.open(io.BytesIO(written)).load()

    def test_the_chunk_goes_after_ihdr(self):
        written = xmp_segments_write(_png(), b"<x:xmpmeta/>")
        assert written.index(b"IHDR") < written.index(b"iTXt")


class TestUnsupportedFormats:
    def test_reading_an_unknown_container_raises(self):
        with pytest.raises(UnsupportedImageError):
            xmp_segments_read(b"GIF89a not really an image")

    def test_writing_an_unknown_container_raises(self):
        with pytest.raises(UnsupportedImageError):
            xmp_segments_write(b"GIF89a not really an image", b"<x:xmpmeta/>")


class TestEndToEnd:
    """Packet and splice together, which is how PR 4 will use them."""

    def test_a_tagged_photo_keeps_its_pixels_and_its_metadata(self):
        original = _jpeg()
        packet = xmp_packet_build(SAMPLE)
        written = xmp_segments_write(original, packet)

        assert _pixels(original) == _pixels(written)
        assert xmp_packet_read(xmp_segments_read(written)) == xmp_packet_read(packet)

    def test_retagging_preserves_another_application_s_work(self):
        theirs = (
            b'<x:xmpmeta xmlns:x="adobe:ns:meta/">'
            b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            b'<rdf:Description rdf:about="" '
            b'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            b"<dc:rights>Theirs</dc:rights>"
            b"</rdf:Description></rdf:RDF></x:xmpmeta>"
        )
        photo = xmp_segments_write(_jpeg(), theirs)

        existing = xmp_segments_read(photo)
        updated = xmp_segments_write(photo, xmp_packet_build(SAMPLE, existing=existing))

        assert b"Theirs" in updated
        assert xmp_packet_read(xmp_segments_read(updated))["rating"] == 5
