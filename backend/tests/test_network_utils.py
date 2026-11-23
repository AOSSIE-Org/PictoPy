import socket
from collections import namedtuple
from typing import Dict, Iterator, List, Optional, Protocol

import pytest

from app.utils.network import (
    network_util_best_candidate,
    network_util_list_candidates,
)

# Mirrors the shapes psutil returns, minus the fields this module ignores.
FakeAddr = namedtuple("FakeAddr", ["family", "address"])
FakeStats = namedtuple("FakeStats", ["isup"])


class InstallInterfaces(Protocol):
    """Signature of the callable the fake_interfaces fixture hands back."""

    def __call__(
        self,
        addrs: Dict[str, List[FakeAddr]],
        stats: Dict[str, FakeStats],
        route_ip: Optional[str] = None,
    ) -> None: ...


def ipv4(address: str) -> FakeAddr:
    return FakeAddr(family=socket.AF_INET, address=address)


def ipv6(address: str) -> FakeAddr:
    return FakeAddr(family=socket.AF_INET6, address=address)


@pytest.fixture
def fake_interfaces(monkeypatch: pytest.MonkeyPatch) -> Iterator[InstallInterfaces]:
    """Install a fake adapter list and default route."""

    def install(
        addrs: Dict[str, List[FakeAddr]],
        stats: Dict[str, FakeStats],
        route_ip: Optional[str] = None,
    ) -> None:
        monkeypatch.setattr(
            "app.utils.network.psutil.net_if_addrs", lambda: addrs, raising=False
        )
        monkeypatch.setattr(
            "app.utils.network.psutil.net_if_stats", lambda: stats, raising=False
        )
        monkeypatch.setattr(
            "app.utils.network.network_util_default_route_ip", lambda: route_ip
        )

    yield install


class TestCandidateFiltering:
    def test_drops_loopback(self, fake_interfaces: InstallInterfaces) -> None:
        fake_interfaces(
            {"lo": [ipv4("127.0.0.1")], "Wi-Fi": [ipv4("10.170.93.60")]},
            {"lo": FakeStats(True), "Wi-Fi": FakeStats(True)},
        )
        assert [c.ip for c in network_util_list_candidates()] == ["10.170.93.60"]

    def test_keeps_link_local(self, fake_interfaces: InstallInterfaces) -> None:
        """
        A 169.254 address usually means DHCP failed, but two devices on the
        same link can still reach each other through it.
        """
        fake_interfaces(
            {"Wi-Fi": [ipv4("169.254.119.169")]}, {"Wi-Fi": FakeStats(True)}
        )
        candidates = network_util_list_candidates()
        assert [c.ip for c in candidates] == ["169.254.119.169"]
        assert candidates[0].is_link_local is True

    def test_ignores_ipv6(self, fake_interfaces: InstallInterfaces) -> None:
        fake_interfaces(
            {"Wi-Fi": [ipv6("fe80::1"), ipv4("192.168.1.5")]},
            {"Wi-Fi": FakeStats(True)},
        )
        assert [c.ip for c in network_util_list_candidates()] == ["192.168.1.5"]

    def test_no_candidates_when_offline(
        self, fake_interfaces: InstallInterfaces
    ) -> None:
        fake_interfaces({"lo": [ipv4("127.0.0.1")]}, {"lo": FakeStats(True)})
        assert network_util_list_candidates() == []
        assert network_util_best_candidate() is None


class TestCandidateRanking:
    def test_default_route_wins_among_live_interfaces(
        self, fake_interfaces: InstallInterfaces
    ) -> None:
        fake_interfaces(
            {"Ethernet 2": [ipv4("10.168.36.61")], "Wi-Fi": [ipv4("10.170.93.60")]},
            {"Ethernet 2": FakeStats(True), "Wi-Fi": FakeStats(True)},
            route_ip="10.170.93.60",
        )
        best = network_util_best_candidate()
        assert best is not None
        assert best.ip == "10.170.93.60"
        assert best.is_default_route

    def test_live_interface_beats_a_downed_default_route(
        self, fake_interfaces: InstallInterfaces
    ) -> None:
        """
        Windows keeps a stale lease and default route on a disconnected
        adapter, and an address there can never accept a connection.
        """
        fake_interfaces(
            {"Wi-Fi": [ipv4("10.170.93.60")], "Ethernet 2": [ipv4("10.168.36.61")]},
            {"Wi-Fi": FakeStats(False), "Ethernet 2": FakeStats(True)},
            route_ip="10.170.93.60",
        )
        best = network_util_best_candidate()
        assert best is not None
        assert best.ip == "10.168.36.61"
        assert best.is_up is True

    def test_virtual_adapters_sort_last(
        self, fake_interfaces: InstallInterfaces
    ) -> None:
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

    def test_link_local_sorts_below_a_routable_address(
        self, fake_interfaces: InstallInterfaces
    ) -> None:
        fake_interfaces(
            {"Wi-Fi": [ipv4("169.254.119.169")], "Ethernet 2": [ipv4("10.168.36.61")]},
            {"Wi-Fi": FakeStats(True), "Ethernet 2": FakeStats(True)},
        )
        assert [c.ip for c in network_util_list_candidates()] == [
            "10.168.36.61",
            "169.254.119.169",
        ]

    def test_link_local_on_real_hardware_beats_a_virtual_adapter(
        self, fake_interfaces: InstallInterfaces
    ) -> None:
        """
        When DHCP has failed everywhere, the real adapter is still the only one
        a second device could be sharing a link with.
        """
        fake_interfaces(
            {
                "Wi-Fi": [ipv4("169.254.119.169")],
                "VMware Network Adapter VMnet1": [ipv4("192.168.65.1")],
            },
            {
                "Wi-Fi": FakeStats(True),
                "VMware Network Adapter VMnet1": FakeStats(True),
            },
        )
        best = network_util_best_candidate()
        assert best is not None
        assert best.ip == "169.254.119.169"

    def test_missing_stats_entry_is_not_fatal(
        self, fake_interfaces: InstallInterfaces
    ) -> None:
        fake_interfaces({"Wi-Fi": [ipv4("10.0.0.5")]}, {})
        assert network_util_list_candidates()[0].is_up is False
