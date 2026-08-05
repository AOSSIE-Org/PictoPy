import socket
from collections import namedtuple

import pytest

from app.utils.network import (
    network_util_best_candidate,
    network_util_list_candidates,
)

# Mirrors the shapes psutil returns, minus the fields this module ignores.
FakeAddr = namedtuple("FakeAddr", ["family", "address"])
FakeStats = namedtuple("FakeStats", ["isup"])


def ipv4(address: str) -> FakeAddr:
    return FakeAddr(family=socket.AF_INET, address=address)


def ipv6(address: str) -> FakeAddr:
    return FakeAddr(family=socket.AF_INET6, address=address)


@pytest.fixture
def fake_interfaces(monkeypatch: pytest.MonkeyPatch):
    """Install a fake adapter list and default route."""

    def install(addrs: dict, stats: dict, route_ip=None) -> None:
        monkeypatch.setattr(
            "app.utils.network.psutil.net_if_addrs", lambda: addrs, raising=False
        )
        monkeypatch.setattr(
            "app.utils.network.psutil.net_if_stats", lambda: stats, raising=False
        )
        monkeypatch.setattr(
            "app.utils.network.network_util_default_route_ip", lambda: route_ip
        )

    return install


class TestCandidateFiltering:
    def test_drops_loopback_and_link_local(self, fake_interfaces):
        fake_interfaces(
            {
                "lo": [ipv4("127.0.0.1")],
                "Ethernet": [ipv4("169.254.119.169")],
                "Wi-Fi": [ipv4("10.170.93.60")],
            },
            {
                "lo": FakeStats(True),
                "Ethernet": FakeStats(True),
                "Wi-Fi": FakeStats(True),
            },
        )
        assert [c.ip for c in network_util_list_candidates()] == ["10.170.93.60"]

    def test_ignores_ipv6(self, fake_interfaces):
        fake_interfaces(
            {"Wi-Fi": [ipv6("fe80::1"), ipv4("192.168.1.5")]},
            {"Wi-Fi": FakeStats(True)},
        )
        assert [c.ip for c in network_util_list_candidates()] == ["192.168.1.5"]

    def test_no_candidates_when_offline(self, fake_interfaces):
        fake_interfaces({"lo": [ipv4("127.0.0.1")]}, {"lo": FakeStats(True)})
        assert network_util_list_candidates() == []
        assert network_util_best_candidate() is None


class TestCandidateRanking:
    def test_default_route_wins(self, fake_interfaces):
        fake_interfaces(
            {
                "Ethernet 2": [ipv4("10.168.36.61")],
                "Wi-Fi": [ipv4("10.170.93.60")],
            },
            {"Ethernet 2": FakeStats(True), "Wi-Fi": FakeStats(True)},
            route_ip="10.170.93.60",
        )
        best = network_util_best_candidate()
        assert best.ip == "10.170.93.60"
        assert best.is_default_route

    def test_virtual_adapters_sort_last(self, fake_interfaces):
        """The case that broke the naive picker: VMware outranking real hardware."""
        fake_interfaces(
            {
                "VMware Network Adapter VMnet1": [ipv4("192.168.65.1")],
                "VMware Network Adapter VMnet8": [ipv4("192.168.220.1")],
                "Wi-Fi": [ipv4("10.170.93.60")],
            },
            {
                "VMware Network Adapter VMnet1": FakeStats(True),
                "VMware Network Adapter VMnet8": FakeStats(True),
                "Wi-Fi": FakeStats(True),
            },
        )
        candidates = network_util_list_candidates()
        assert candidates[0].ip == "10.170.93.60"
        assert candidates[0].looks_virtual is False
        assert all(c.looks_virtual for c in candidates[1:])

    def test_down_interface_sorts_below_up(self, fake_interfaces):
        """A disconnected adapter can keep a stale DHCP lease that still looks real."""
        fake_interfaces(
            {
                "Wi-Fi": [ipv4("10.170.93.60")],
                "Ethernet 2": [ipv4("10.168.36.61")],
            },
            {"Wi-Fi": FakeStats(False), "Ethernet 2": FakeStats(True)},
        )
        candidates = network_util_list_candidates()
        assert candidates[0].ip == "10.168.36.61"
        assert candidates[-1].is_up is False

    def test_missing_stats_entry_is_not_fatal(self, fake_interfaces):
        fake_interfaces({"Wi-Fi": [ipv4("10.0.0.5")]}, {})
        assert network_util_list_candidates()[0].is_up is False
