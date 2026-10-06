"""Tests for net_dns.resolver."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import dns.exception
import dns.resolver
import pytest

from net_dns.resolver import (
    SUPPORTED_TYPES,
    ResolveError,
    resolve,
    resolve_many,
)


def _fake_answer(values: list[str]) -> list[MagicMock]:
    return [MagicMock(__str__=lambda self, v=v: v) for v in values]


def test_unsupported_record_type_raises() -> None:
    with pytest.raises(ResolveError, match="unsupported record type"):
        resolve("example.com", "BOGUS")


def test_successful_a_lookup() -> None:
    fake = [MagicMock()]
    fake[0].__str__ = lambda self: "1.2.3.4"

    with patch("dns.resolver.Resolver.resolve", return_value=fake):
        result = resolve("example.com", "A")

    assert result.ok
    assert result.values == ["1.2.3.4"]
    assert result.record_type == "A"
    assert result.target == "example.com"


def test_nxdomain_returns_error_not_raise() -> None:
    with patch(
        "dns.resolver.Resolver.resolve",
        side_effect=dns.resolver.NXDOMAIN,
    ):
        result = resolve("does-not-exist.example", "A")

    assert not result.ok
    assert "NXDOMAIN" in (result.error or "")


def test_timeout_returns_error() -> None:
    with patch(
        "dns.resolver.Resolver.resolve",
        side_effect=dns.exception.Timeout,
    ):
        result = resolve("example.com", "A")

    assert not result.ok
    assert "timed out" in (result.error or "")


def test_mx_formatting() -> None:
    rdata = MagicMock()
    rdata.preference = 10
    rdata.exchange = "mail.example.com"

    with patch("dns.resolver.Resolver.resolve", return_value=[rdata]):
        result = resolve("example.com", "MX")

    assert result.values == ["10 mail.example.com"]


def test_srv_formatting() -> None:
    rdata = MagicMock()
    rdata.priority = 1
    rdata.weight = 5
    rdata.port = 443
    rdata.target = "svc.example.com"

    with patch("dns.resolver.Resolver.resolve", return_value=[rdata]):
        result = resolve("_https._tcp.example.com", "SRV")

    assert result.values == ["1 5 443 svc.example.com"]


def test_nameserver_is_applied() -> None:
    fake_resolver = MagicMock()
    fake_resolver.resolve.return_value = []

    with patch("dns.resolver.Resolver", return_value=fake_resolver):
        resolve("example.com", "A", nameserver="1.1.1.1")

    assert fake_resolver.nameservers == ["1.1.1.1"]


def test_resolve_many_returns_one_per_type() -> None:
    with patch("dns.resolver.Resolver.resolve", return_value=[]):
        results = resolve_many("example.com", ["A", "AAAA", "MX"])

    assert [r.record_type for r in results] == ["A", "AAAA", "MX"]


def test_supported_types_are_uppercase() -> None:
    assert all(t == t.upper() for t in SUPPORTED_TYPES)