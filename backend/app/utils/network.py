"""
LAN interface discovery for share URLs.

Picking the wrong address produces a QR code that silently never loads, so
candidates are ranked rather than guessed at and the caller is expected to let
the user override the top pick.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import List, Optional

import psutil

# Adapter name fragments that are almost never the address a phone can reach.
# Deprioritised rather than dropped: on some machines the only usable address
# really is behind one of these.
VIRTUAL_HINTS = (
    "vethernet",
    "wsl",
    "hyper-v",
    "virtualbox",
    "vboxnet",
    "vmware",
    "vmnet",
    "docker",
    "br-",
    "veth",
    "tailscale",
    "zerotier",
    "utun",
    "tun",
    "tap",
    "loopback",
    "bluetooth",
)


@dataclass
class InterfaceCandidate:
    """One address the share server could plausibly be reached on."""

    interface: str
    ip: str
    is_default_route: bool
    looks_virtual: bool
    is_up: bool

    @property
    def rank(self) -> tuple:
        # Lower sorts first.
        return (
            0 if self.is_default_route else 1,
            0 if self.is_up else 1,
            1 if self.looks_virtual else 0,
            self.interface.lower(),
        )


def network_util_default_route_ip() -> Optional[str]:
    """
    The address the OS would use to reach the internet.

    UDP connect() only fixes the socket's local endpoint; no packet is sent, so
    this works with no connectivity and never blocks.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def _looks_virtual(interface: str) -> bool:
    name = interface.lower()
    return any(hint in name for hint in VIRTUAL_HINTS)


def network_util_list_candidates() -> List[InterfaceCandidate]:
    """Every reachable IPv4 address on this machine, best guess first."""
    route_ip = network_util_default_route_ip()
    stats = psutil.net_if_stats()
    candidates: List[InterfaceCandidate] = []

    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family != socket.AF_INET:
                continue
            ip = addr.address
            # Loopback cannot be reached from another device, and a 169.254
            # address means DHCP never answered — a symptom, not an address.
            if ip.startswith("127.") or ip.startswith("169.254."):
                continue
            candidates.append(
                InterfaceCandidate(
                    interface=interface,
                    ip=ip,
                    is_default_route=(ip == route_ip),
                    looks_virtual=_looks_virtual(interface),
                    is_up=stats[interface].isup if interface in stats else False,
                )
            )

    return sorted(candidates, key=lambda candidate: candidate.rank)


def network_util_best_candidate() -> Optional[InterfaceCandidate]:
    """The address to advertise when the user has not chosen one."""
    candidates = network_util_list_candidates()
    return candidates[0] if candidates else None
