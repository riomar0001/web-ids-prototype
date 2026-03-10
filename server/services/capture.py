"""
Network packet capture using Scapy.

Runs a background sniff bounded by a BPF filter that targets the
client IP and server port of a given HTTP request.
"""

import logging
import threading

from scapy.all import PacketList, sniff

from server.config import SNIFF_TIMEOUT

logger = logging.getLogger("ids")


class PacketCapture:
    """Captures packets matching a client–server flow in a daemon thread."""

    def __init__(self, client_ip: str, server_port: int) -> None:
        self.client_ip = client_ip
        self.server_port = server_port
        self.packets: PacketList = PacketList()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Begin sniffing in the background."""
        bpf = f"host {self.client_ip} and port {self.server_port}"
        self._thread = threading.Thread(
            target=self._sniff,
            args=(bpf,),
            daemon=True,
        )
        self._thread.start()

    def _sniff(self, bpf: str) -> None:
        try:
            self.packets = sniff(
                iface="eth0",   # Docker container's primary interface; avoids
                                # accidentally capturing loopback or other ifaces
                filter=bpf,
                timeout=SNIFF_TIMEOUT,
                store=True,
            )
        except Exception as exc:
            logger.warning("Scapy sniff error: %s", exc)
            self.packets = PacketList()

    def wait(self) -> None:
        """Block until the capture thread completes."""
        if self._thread:
            self._thread.join(timeout=SNIFF_TIMEOUT + 1)
