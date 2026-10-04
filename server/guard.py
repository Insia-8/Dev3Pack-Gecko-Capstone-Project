"""is_public_url: refuse anything a server should not fetch on someone else's say-so."""
import ipaddress
import socket
from urllib.parse import urlparse


def is_public_url(url: str) -> bool:
    try:
        parts = urlparse(url)
        host = parts.hostname
    except ValueError:
        return False
    if parts.scheme != "https" or not host:
        return False
    try:
        addrs = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, parts.port or 443, proto=socket.IPPROTO_TCP)
        except (socket.gaierror, UnicodeError, OSError):
            # Decision: a name that does not resolve is refused. We cannot prove it is
            # public, and an attacker-controlled DNS answer could change later.
            return False
        addrs = [ipaddress.ip_address(i[4][0].split("%")[0]) for i in infos]
    if not addrs:
        return False
    for a in addrs:
        if getattr(a, "ipv4_mapped", None):
            a = a.ipv4_mapped
        if not a.is_global or a.is_multicast:
            return False
    return True