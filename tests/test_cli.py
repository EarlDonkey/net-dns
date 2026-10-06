"""Tests for net_dns.cli."""

from __future__ import annotations

import json
from unittest.mock import patch

from net_dns.cli import main
from net_dns.resolver import LookupResult


def _patch_results(results: list[LookupResult]):
    return patch("net_dns.cli.resolve_many", return_value=results)


def test_human_output_success(capsys) -> None:
    results = [LookupResult("example.com", "A", ["1.2.3.4"])]

    with _patch_results(results):
        code = main(["example.com"])

    out = capsys.readouterr().out
    assert code == 0
    assert "example.com" in out
    assert "1.2.3.4" in out


def test_json_output(capsys) -> None:
    results = [
        LookupResult("example.com", "A", ["1.2.3.4"]),
        LookupResult("example.com", "MX", ["10 mail.example.com"]),
    ]

    with _patch_results(results):
        code = main(["example.com", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["target"] == "example.com"
    assert len(payload["results"]) == 2
    assert payload["results"][0]["values"] == ["1.2.3.4"]


def test_any_expands_to_all_types(capsys) -> None:
    results = [LookupResult("example.com", "A", ["1.2.3.4"])]

    with _patch_results(results) as mock:
        main(["example.com", "-t", "any"])

    passed_types = mock.call_args.args[1]
    assert "A" in passed_types
    assert "MX" in passed_types
    assert "AAAA" in passed_types


def test_all_failed_returns_exit_1() -> None:
    results = [LookupResult("example.com", "A", error="NXDOMAIN")]

    with _patch_results(results):
        code = main(["example.com"])

    assert code == 1


def test_partial_failure_returns_exit_0() -> None:
    results = [
        LookupResult("example.com", "A", ["1.2.3.4"]),
        LookupResult("example.com", "MX", error="no MX records found"),
    ]

    with _patch_results(results):
        code = main(["example.com", "-t", "A", "-t", "MX"])

    assert code == 0