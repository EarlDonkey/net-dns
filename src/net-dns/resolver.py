"""Core DNS resolution logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import dns.exception
import dns.resolver

# Record types we support and their human-friendly names.
SUPPORTED_TYPES: tuple[str, ...] = (
    "A",
    "AAAA",
    "CNAME",
    "MX",
    "NS",
    "TXT",
    "SOA",
    "SRV",
    "PTR",
    "CAA",
)

DEFAULT_TIMEOUT = 5.0
DEFAULT_LIFETIME = 10.0


class ResolveError(Exception):
    """Raised when a DNS lookup fails in a non-recoverable way."""


@dataclass
class LookupResult:
    """Result of a DNS lookup for a single (name, type) pair."""

    target: str
    record_type: str
    values: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "target": self.target,
            "type": self.record_type,
            "values": self.values,
        }
        if self.error:
            out["error"] = self.error
        return out


def _format_rdata(record_type: str, rdata: Any) -> str:
    """Render a dnspython rdata object as a friendly string."""
    if record_type == "MX":
        return f"{rdata.preference} {rdata.exchange}"
    if record_type == "SRV":
        return f"{rdata.priority} {rdata.weight} {rdata.port} {rdata.target}"
    if record_type == "SOA":
        return (
            f"{rdata.mname} {rdata.rname} "
            f"serial={rdata.serial} refresh={rdata.refresh} "
            f"retry={rdata.retry} expire={rdata.expire} minimum={rdata.minimum}"
        )
    if record_type == "CAA":
        return f'{rdata.flags} {rdata.tag} "{rdata.value}"'
    # A, AAAA, CNAME, NS, PTR, TXT
    return str(rdata)


def resolve(
    target: str,
    record_type: str = "A",
    *,
    nameserver: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    lifetime: float = DEFAULT_LIFETIME,
) -> LookupResult:
    """Resolve `target` for `record_type`.

    Never raises for expected DNS failures — returns a LookupResult with
    `.error` set instead. Raises ResolveError only for programmer errors
    (unsupported record types).
    """
    record_type = record_type.upper()
    if record_type not in SUPPORTED_TYPES:
        raise ResolveError(
            f"unsupported record type: {record_type}. "
            f"Supported: {', '.join(SUPPORTED_TYPES)}"
        )

    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = lifetime
    if nameserver:
        resolver.nameservers = [nameserver]

    result = LookupResult(target=target, record_type=record_type)

    try:
        answers = resolver.resolve(target, record_type)
    except dns.resolver.NXDOMAIN:
        result.error = "NXDOMAIN (name does not exist)"
        return result
    except dns.resolver.NoAnswer:
        result.error = f"no {record_type} records found"
        return result
    except dns.resolver.NoNameservers:
        result.error = "no nameservers available or all refused"
        return result
    except dns.exception.Timeout:
        result.error = "query timed out"
        return result
    except dns.exception.DNSException as exc:
        result.error = f"{type(exc).__name__}: {exc}"
        return result

    result.values = [_format_rdata(record_type, rdata) for rdata in answers]
    return result


def resolve_many(
    target: str,
    record_types: list[str],
    *,
    nameserver: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    lifetime: float = DEFAULT_LIFETIME,
) -> list[LookupResult]:
    """Resolve multiple record types for the same target."""
    return [
        resolve(
            target,
            rt,
            nameserver=nameserver,
            timeout=timeout,
            lifetime=lifetime,
        )
        for rt in record_types
    ]