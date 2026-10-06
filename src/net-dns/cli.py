"""Command-line interface for net-dns."""

from __future__ import annotations

import argparse
import json
import sys
from typing import NoReturn

from net_dns import __version__
from net_dns.resolver import (
    SUPPORTED_TYPES,
    LookupResult,
    ResolveError,
    resolve_many,
)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BAD_ARGS = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="net-dns",
        description="Fast, scriptable DNS lookup tool.",
        epilog="Only query domains you are authorized to inspect.",
    )
    parser.add_argument(
        "target",
        help="Domain name or IP address (for PTR) to query.",
    )
    parser.add_argument(
        "-t",
        "--type",
        dest="types",
        action="append",
        choices=[t.lower() for t in SUPPORTED_TYPES] + ["any"],
        help=(
            "Record type. Repeatable (e.g. -t A -t MX). "
            "Defaults to A. Use 'any' to try all common types."
        ),
    )
    parser.add_argument(
        "-s",
        "--server",
        dest="nameserver",
        default=None,
        help="Custom nameserver (e.g. 1.1.1.1).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Per-query timeout in seconds (default: 5).",
    )
    parser.add_argument(
        "-j",
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"net-dns {__version__}",
    )
    return parser


def _normalize_types(types: list[str] | None) -> list[str]:
    if not types:
        return ["A"]
    expanded: list[str] = []
    for t in types:
        if t.lower() == "any":
            for candidate in SUPPORTED_TYPES:
                if candidate not in expanded:
                    expanded.append(candidate)
        else:
            upper = t.upper()
            if upper not in expanded:
                expanded.append(upper)
    return expanded


def _print_human(results: list[LookupResult]) -> None:
    target = results[0].target if results else ""
    print(target)
    for result in results:
        if result.ok:
            for value in result.values:
                print(f"  {result.record_type:<6} {value}")
        else:
            print(f"  {result.record_type:<6} [error] {result.error}")


def _print_json(results: list[LookupResult]) -> None:
    payload = {
        "target": results[0].target if results else None,
        "results": [r.to_dict() for r in results],
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _fail(message: str, code: int) -> NoReturn:
    print(f"net-dns: error: {message}", file=sys.stderr)
    sys.exit(code)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    record_types = _normalize_types(args.types)

    try:
        results = resolve_many(
            args.target,
            record_types,
            nameserver=args.nameserver,
            timeout=args.timeout,
        )
    except ResolveError as exc:
        _fail(str(exc), EXIT_BAD_ARGS)

    if args.as_json:
        _print_json(results)
    else:
        _print_human(results)

    # Exit non-zero if every lookup failed (useful for shell scripts).
    if results and all(not r.ok for r in results):
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())