# net-dns

> Fast, scriptable DNS lookup tool with JSON output.

`net-dns` is a small CLI for querying DNS records across all common types. It's
designed for scripting: human-readable by default, `--json` when you need it,
sane exit codes, and no surprises.

## Features

- Query **A, AAAA, CNAME, MX, NS, TXT, SOA, SRV, PTR, CAA** records
- `-t any` to try all common types at once
- `--json` for machine-readable output
- Custom nameserver support (`-s 1.1.1.1`)
- Per-query timeout control
- Non-zero exit when every lookup fails (great for shell scripts)
- Zero config, single dependency (`dnspython`)

## Install

### From source (recommended for now)

```bash
git clone https://github.com/YOUR_USERNAME/net-dns.git
cd net-dns
pipx install .
```

### Development install

```bash
git clone https://github.com/YOUR_USERNAME/net-dns.git
cd net-dns
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
# Default: A record
net-dns example.com

# Specific record type
net-dns example.com -t AAAA
net-dns example.com -t MX

# Multiple types
net-dns example.com -t A -t AAAA -t MX

# All common types
net-dns example.com -t any

# JSON output
net-dns example.com --json

# Custom nameserver
net-dns example.com -s 1.1.1.1

# Shorter timeout
net-dns example.com --timeout 2
```

## Example output

```
$ net-dns github.com -t A -t MX
github.com
  A      140.82.121.3
  A      140.82.121.4
  MX     0 smtp.github.com
```

```json
$ net-dns github.com -t A --json
{
  "target": "github.com",
  "results": [
    {
      "target": "github.com",
      "type": "A",
      "values": ["140.82.121.3", "140.82.121.4"]
    }
  ]
}
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Success (at least one record returned) |
| `1`  | Every lookup failed (NXDOMAIN, timeout, etc.) |
| `2`  | Bad arguments |

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Type-check
mypy src
```

## ⚠️ Legal

Only query domains you own or have explicit permission to inspect. Unauthorized
enumeration may violate terms of service or local law.

## License

MIT — see [LICENSE](LICENSE).