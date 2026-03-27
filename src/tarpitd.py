#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# =============================================================================
# Manual: tarpitd.py.1
# -----------------------------------------------------------------------------
_MANUAL_TARPITD_PY_1 = r""" 
## NAME

tarpitd.py - making a port into tarpit

## SYNOPSIS

    tarpitd.py <subcommand> [options]

Available subcommands:

* `serve` - Start one or more tarpit services
* `manual` - Display built-in manual pages
* `ctl` - Control and get information from running supervisor

## DESCRIPTION

tarpitd.py listens on specified network ports and purposefully delays or
troubles clients that connect to it. This tool can be used to tie up network
connections by delivering slow or malformed responses, potentially keeping
client connections open for extended periods.

## SUBCOMMANDS

### `serve`

Start one or more tarpit services.

#### Synopsis

    tarpitd.py serve [-h] [-v] [-r RATE] [-c FILE]
        [-t {none,access,request}] [--log-trace FILE]
        [-e [{check, none}]] -p PATTERN:HOST:PORT [PATTERN:HOST:PORT ...]

#### Options

#### `-c, --config FILE`

Load configuration from file. Cannot be used together with `-p/--pattern`.

#### `-p, --pattern PATTERN:HOST:PORT [PATTERN:HOST:PORT ...]`

Start a tarpit pattern on the specified host and port (required unless using
`-c/--config`).

The name of PATTERN is case-insensitive. For a complete list of supported
patterns, see the "TARPIT PATTERN" section below.

#### `-r RATE, --rate-limit RATE`

Set data transfer rate limit. Tarpits pattern has their own default value.

A positive value limits the transfer speed to RATE *bytes* per second. A
negative value causes the program to send one byte every |RATE| seconds
(effectively 1/|RATE| *bytes* per second).

#### `-t, --trace {none,access,request}`

Set client trace level. Default is `none`.

* `none`: No client tracing
* `access`: Log client connections and disconnections
* `request`: Log client connections, disconnections, and request data

#### `--log-trace [FILE]`

Specify output file for client trace logs. Optional.

The output is in jsonl format. Logs to stdout if FILE is left blank.

#### `-e, --validate-client [{check, none}]`

Examine the client before sending a response. Enabled by default. Use `-e
none` to disable it.

The current implementation checks the first few bytes of the request to
confirm that the client is using the corresponding protocol.

### `manual`

Display built-in manual pages.

#### Synopsis

    tarpitd.py manual [page]

#### Options

#### `page`

Name of the manual page to display. Default is `tarpitd.py.1`.

Available manual pages include:

* tarpitd.py.1 : Program usage
* tarpitd.conf.5 : Configuration file format

## TARPIT PATTERN

### HTTP

#### http_endless_header

Tested with: Firefox, Chromium, curl

Sends an endless stream of HTTP header lines (specifically, `Set-Cookie:`).
Some clients will wait indefinitely for the header to end (or for a blank line
indicating the end of the headers), while others (like curl) may have header
size restrictions and close the connection once the limit is reached.

#### http_bad_site

Tested with: Firefox, Chromium

Responds to the client with a small HTML page containing many links and a
dead-loop script. Browsers that support JavaScript will get stuck, and those
links may cause crawlers to repeatedly pull the webpage.

#### http_deflate_html_bomb

Tested with: Firefox, Chromium

Sends a badly formed HTML document compressed using the deflate (zlib)
algorithm. Most clients will consume significant CPU resources attempting to
parse the malformed HTML.

Note: The response is always compressed with deflate regardless of client
support, as serving uncompressed output might waste bandwidth. When using
curl, use the `--compressed` option to trigger decompression and ensure you
have sufficient disk space to handle the decompressed content.

#### http_deflate_size_bomb

Tested with: Firefox, Chromium, curl

Feeds the client a large amount of compressed zero data. The current
implementation sends a compressed 1 MB file that decompresses to approximately
1 GB, with added invalid HTML to further confuse the client.

Note: The deflate compression algorithm has its maximum compression rate limit
at 1030.3:1.

#### http_fake_auth

Tested with: curl

Responds with HTTP 401 Unauthorized status and a `WWW-Authenticate` header
requesting Basic authentication. Clients may retry with credentials, but the
server will always reject them, potentially causing automated tools to loop.

### SSH

#### endlessh

Tested with: OpenSSH

endlessh is a well-known SSH tarpit that traps SSH clients by sending endless
banner messages. Although named “endlessh”, it does not implement the full SSH
protocol; it simply emits continuous banner data. As a result, port scanners
(such as nmap and censys) will not mark the original version as running a true
SSH service. tarpitd.py have this problem fixed by examining the client and
sending SSH identifier to scanners. What's more, openssh will only accept 1024
line of banner before disconnect.

#### ssh_trans_hold

Tested with: OpenSSH

This tarpit mimics an SSH server's initial handshake by sending valid SSH
transport messages and key exchange information (per IETF RFC 4253). However,
instead of completing the exchange, it repeatedly sends `SSH_MSG_IGNORE`
messages. Although clients are supposed to ignore these messages according to
the standard, the continual stream keeps the connection open indefinitely.

Note: The implementation advertises itself as OpenSSH 8.9 on Ubuntu and
replays a pre-recorded SSH key exchange. Future updates may alter aspects of
this behavior.

### FTP

#### ftp_endless_motd

Tested with: curl

Sends an endless stream of FTP message-of-the-day (MOTD) lines after a
successful login response. FTP clients will continue to wait for the
complete message, keeping the connection open indefinitely.

### SMTP

#### smtp_endless_ehlo

Tested with: curl

Responds to the client's EHLO/HELO command with an endless stream of
ESMTP capability lines. SMTP clients will wait for the complete list
of server capabilities, effectively keeping the connection stuck.

### TLS

#### tls_slow_hello

Tested with: openssl (cli), gnutls (cli)

Responds with a long (but still valid) server hello. Clients will read the
complete message before the connection is closed.

#### tls_endless_hello_request

Tested with: openssl (cli), curl (with openssl)

Sends an endless series of HelloRequest messages to the client. According to
IETF RFC 5246 (the TLS 1.2 specification), clients should ignore extra
HelloRequest messages during the negotiation phase, effectively keeping the
connection open. This will affect all clients using OpenSSL, including curl.

Firefox will report a timeout after 10 seconds. GNU TLS (and wget using it)
will disconnect immediately, complaining about handshake failure.

### MISC

#### egsh_aminoas

Tested with: OpenSSH

An alternative to endlessh, this service not only keeps connections open but
also adds a cultural touch.

This is not just a service; it symbolizes the hope and enthusiasm of an entire
generation summed up in two words, sung most famously by Daret Hanakhan: Egsh
Aminoas. When clients connect, they will randomly receive a quote from
classical Aminoas culture, and tarpitd.py will log the same quote
simultaneously.

## EXAMPLES

### Using the `manual` subcommand

Display the main manual:

    tarpitd.py manual

Display the configuration file manual:

    tarpitd.py manual tarpitd.conf.5

### Using the `serve` subcommand

Start an endlessh tarpit:

    tarpitd.py serve -p endlessh:0.0.0.0:2222

Start an endless HTTP tarpit with a 2-second per-byte delay:

    tarpitd.py serve -r -2 -p http_endless_header:0.0.0.0:8088

Start an endless HTTP tarpit with a rate limit of 1 KB/s:

    tarpitd.py serve -r 1024 -p HTTP_DEFLATE_HTML_BOMB:0.0.0.0:8088

Start two different HTTP tarpit services concurrently (the name of the pattern
is case-insensitive):

    tarpitd.py serve -p http_deflate_html_bomb:127.0.0.1:8080 \
                     http_endless_header:0.0.0.0:8088

Start tarpit from configuration file:

    tarpitd.py serve -c /path/to/config.toml

### Using the `ctl` subcommand

The `ctl` subcommand is used to communicate with a running supervisor process
via a Unix domain socket.

#### `ctl ping`

Checks if the supervisor is running:

    tarpitd.py ctl ping

This will display:
- Server name
- Server version
- Status (Running)

#### `ctl status`

Shows detailed status information:

    tarpitd.py ctl status

This will display:
- Server name and version
- Uptime (time since server started)
- Event buffer usage (events currently stored / total buffer size)

##### Options

- `-s, --socket PATH` - Specify the Unix domain socket path (default: /tmp/tarpitd_u<UID>.sock)
  Can also be set via environment variable `TARPITD_SOCKET`.

#### `ctl logs`

Query and display event logs from the supervisor.

    tarpitd.py ctl logs [-r RANGE] [-c CATALOG] [-f FORMAT]
                        [--peer-ip IP] [--tarpit NAME] [--type TYPE]

##### Options

- `-r, --range START,END` - Range of events to display (1-indexed, negative for reverse).
  Examples: `-r 1,5` (first 5 events), `-r -1,-5` (last 5 events). Default: `1,100`
- `-c, --catalog CATALOG` - Catalog to query (currently only 'events'). Default: `events`
- `-f, --format FORMAT` - Output format: 'cli' (human-readable) or 'jsonl'. Default: `cli`
- `--peer-ip IP` - Filter by peer IP address. Supports exact match, wildcard (e.g., `192.168.1.*`), or CIDR (e.g., `192.168.1.0/24`)
- `--tarpit NAME` - Filter by tarpit name
- `--type TYPE` - Filter by event type (e.g., `conn_open`, `conn_close`)

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

------

> This program was made on the lands of
  the Aminoac people of the Amacinoas Nation.
  We pay our respects to their Elders, past and present.
  Sovereignty was never ceded.
"""
# =============================================================================

# =============================================================================
# Manual: tarpitd.conf.5
# -----------------------------------------------------------------------------
_MANUAL_TARPITD_CONF_5 = r""" 
## NAME

tarpitd.conf - configuration file of tarpitd

## DESCRIPTION

It is a TOML format file.

## `[tarpits.<name>]` Table

#### `<name>`

Name of this tarpit.

For reference in log output. Has no effect on behavior.

#### `pattern=` (str)

Specifies the tarpit pattern.

The name of the pattern is case-insensitive. For a complete list of supported
patterns, see [tarpit.py(1)](./tarpitd.py.1.md).

#### `bind=` (table)

A list of addresses and ports to listen on.

Every item in this list should contain `host` and `port` values; see the
example below.

#### `rate_limit=` (int)

Sets the data transfer rate limit.

Follows the same rule as [tarpit.py(1)](./tarpitd.py.1.md).

#### `max_clients=` (int)

The maximum number of clients the server will handle. This is calculated per
bind port.

#### `client_validation=` (bool)

Validate the client before sending a response.

#### `trace=` (int or str)

Set client trace level.

Accepts integer values (0, 1, 2) or string values:

* `0` or `"none"`: No client tracing
* `1` or `"access"`: Log client connections and disconnections
* `2` or `"request"`: Log client connections, disconnections, and request data

Client validation result is logged with access log.

## `[logging]` Table

#### `main=` (str)

Path to the main log file. Special value `<stdout>` and `<stderr>` is
supported.

Default is `<stderr>`.

#### `level=` (str)

Log level.

Accept: `debug`, `info`, `warning`, `error`, `critical`. Default is `warning`.

#### `trace=` (str)

Path to the trace log file. Special value `<stdout>` and `<stderr>` is
supported.

Default is `<stdout>`.

## Example

  [tarpits]
  [tarpits.my_cool_ssh_tarpit]
  pattern = "ssh_trans_hold"
  trace = 1
  client_validation = true
  max_clients = 8152
  rate_limit = -2
  bind = [{ host = "127.0.0.1", port = "2222" }]

  [tarpits.http_tarpit]
  pattern = "http_endless_header"
  bind = [
    { host = "127.0.0.1", port = "8080" },
    { host = "::1", port = "8888" },
  ]

  [tarpits.tls_tarpit]
  pattern = "tls_slow_hello"
  rate_limit = 1
  bind = [
    { host = "127.0.0.1", port = "8443" },
  ]

  [logging]
  trace = "./client_trace.log"

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

------

> This program was made on the lands of
  the Aminoac people of the Amacinoas Nation.
  We pay our respects to their Elders, past and present.
  Sovereignty was never ceded.
"""
# =============================================================================

__version__ = "0.1.0"

# ruff: noqa: E402
import asyncio
import random
import logging
import enum
import zlib
import http
import sys
import json
import dataclasses
import time
import typing
import copy
import os
import socket
import sqlite3
import platform
import gc

# module for cli use only will be import when needed

## Helper things


class BytesLiteralEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return repr(o)
        elif isinstance(o, bytearray):
            return repr(o)[10:-1]
        return json.JSONEncoder.default(self, o)


def _get_default_socket_path() -> str:
    """Return default Unix domain socket path based on user ID."""
    return f"/tmp/tarpitd_u{os.getuid()}.sock"


class EventStore:
    """SQLite-based event storage for querying and persistence."""

    def __init__(
        self,
        db_path: str = ":memory:",
        max_size_bytes: int = 8 * 1024 * 1024,  # 8MB default
        prune_count: int = 256,
    ):
        self.db_path = db_path
        self._is_memory = db_path == ":memory:"
        self._max_size = max_size_bytes
        self._prune_count = prune_count
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Initialize database schema."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                ev_type TEXT NOT NULL,
                tarpit_name TEXT,
                tarpit_pattern TEXT,
                peer_ip TEXT,
                peer_port INTEGER,
                local_ip TEXT,
                local_port INTEGER,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_events_time
                ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_events_peer_ip
                ON events(peer_ip);
            CREATE INDEX IF NOT EXISTS idx_events_tarpit
                ON events(tarpit_name);
            CREATE INDEX IF NOT EXISTS idx_events_type
                ON events(ev_type);
        """)
        self._conn.commit()

    def append(self, event) -> None:
        """Store an event (ConnEvent or WorkerEvent)."""
        peer_ip, peer_port = None, None
        local_ip, local_port = None, None

        if hasattr(event, "peername") and event.peername:
            peer_ip, peer_port = event.peername[0], event.peername[1]
        if hasattr(event, "sockname") and event.sockname:
            local_ip, local_port = event.sockname[0], event.sockname[1]

        metadata = None
        if hasattr(event, "metadata") and event.metadata:
            metadata = json.dumps(event.metadata)

        self._conn.execute(
            """
            INSERT INTO events
                (timestamp, ev_type, tarpit_name, tarpit_pattern,
                 peer_ip, peer_port, local_ip, local_port, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.time,
                event.ev_type,
                getattr(event, "tarpit_name", None),
                getattr(event, "tarpit_pattern", None),
                peer_ip,
                peer_port,
                local_ip,
                local_port,
                metadata,
            ),
        )
        self._conn.commit()

        # Check size limit and prune if needed
        self._prune_if_needed()

    def _prune_if_needed(self) -> None:
        """Remove oldest events if size exceeds limit."""
        current_size = self.get_size()
        if current_size > self._max_size:
            logging.warning(
                "Event store size (%d bytes) exceeds limit (%d bytes), "
                "pruning oldest %d events",
                current_size,
                self._max_size,
                self._prune_count,
            )
            # Delete oldest N events
            self._conn.execute(
                "DELETE FROM events WHERE id IN ("
                "SELECT id FROM events ORDER BY id ASC LIMIT ?"
                ")",
                (self._prune_count,),
            )
            self._conn.commit()
            # Vacuum to reclaim space
            self._conn.execute("VACUUM")
            self._conn.commit()
            logging.info(
                "Pruned %d events, new size: %d bytes",
                self._prune_count,
                self.get_size(),
            )

    def query(
        self,
        catalog: str = "events",
        start: int = 1,
        end: int = 100,
        peer_ip: str | None = None,
        tarpit_name: str | None = None,
        ev_type: str | None = None,
    ) -> list[dict]:
        """Query events with filters and range.

        Args:
            catalog: Table name (currently only 'events')
            start: Start row (1-indexed, negative for reverse from end)
            end: End row (1-indexed, negative for reverse from end)
            peer_ip: Filter by peer IP address
            tarpit_name: Filter by tarpit name
            ev_type: Filter by event type

        Returns:
            List of event dictionaries in requested order
        """
        if catalog != "events":
            raise ValueError(f"Unknown catalog: {catalog}")

        # Build WHERE clause
        where_clauses = []
        params = []

        if peer_ip:
            # Support wildcard patterns (192.168.1.%) and CIDR (192.168.1.0/24)
            if "/" in peer_ip:
                # CIDR notation - convert to range (simplified)
                import ipaddress

                try:
                    network = ipaddress.ip_network(peer_ip, strict=False)
                    # For simplicity, use LIKE with the network prefix
                    # e.g., 192.168.1.0/24 -> peer_ip LIKE '192.168.1.%'
                    prefix = str(network.network_address)
                    octets = prefix.split(".")
                    prefix_len = network.prefixlen
                    if prefix_len == 8:
                        pattern = f"{octets[0]}.%"
                    elif prefix_len == 16:
                        pattern = f"{octets[0]}.{octets[1]}.%"
                    elif prefix_len == 24:
                        pattern = f"{octets[0]}.{octets[1]}.{octets[2]}.%"
                    else:
                        # For other prefix lengths, use exact match
                        # (SQLite doesn't support proper IP range queries)
                        pattern = prefix.rstrip("0").rstrip(".") + "%"
                    where_clauses.append("peer_ip LIKE ?")
                    params.append(pattern)
                except ValueError:
                    # Invalid CIDR, fall back to exact match
                    where_clauses.append("peer_ip = ?")
                    params.append(peer_ip)
            elif (
                "*" in peer_ip
                or "?" in peer_ip
                or "%" in peer_ip
                or "_" in peer_ip
            ):
                # Wildcard pattern - convert * and ? to SQL wildcards (% and _)
                pattern = peer_ip.replace("*", "%").replace("?", "_")
                where_clauses.append("peer_ip LIKE ?")
                params.append(pattern)
            else:
                # Exact match
                where_clauses.append("peer_ip = ?")
                params.append(peer_ip)
        if tarpit_name:
            where_clauses.append("tarpit_name = ?")
            params.append(tarpit_name)
        if ev_type:
            where_clauses.append("ev_type = ?")
            params.append(ev_type)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Determine ordering based on range direction
        if start < 0 or end < 0:
            # Using negative indices - need to determine total count first
            cursor = self._conn.execute(
                f"SELECT COUNT(*) FROM events {where_sql}", params
            )
            total = cursor.fetchone()[0]

            # Convert negative indices
            start_idx = total + start + 1 if start < 0 else start
            end_idx = total + end + 1 if end < 0 else end
        else:
            start_idx, end_idx = start, end

        # Determine direction and calculate offset/limit
        if start_idx <= end_idx:
            # Forward order: ASC
            order = "ASC"
            limit = end_idx - start_idx + 1
            offset = start_idx - 1
        else:
            # Reverse order: DESC
            order = "DESC"
            limit = start_idx - end_idx + 1
            # For DESC order, offset needs to skip from the end
            # First get total to calculate proper offset
            cursor = self._conn.execute(
                f"SELECT COUNT(*) FROM events {where_sql}",
                params[: len(params)],
            )
            total = cursor.fetchone()[0]
            offset = total - start_idx

        query = f"""
            SELECT * FROM events
            {where_sql}
            ORDER BY id {order}
            LIMIT ? OFFSET ?
        """
        params.extend([limit, max(0, offset)])

        cursor = self._conn.execute(query, params)
        rows = cursor.fetchall()

        # Convert rows to dicts
        result = []
        for row in rows:
            d = dict(row)
            if d["metadata"]:
                d["metadata"] = json.loads(d["metadata"])
            result.append(d)

        return result

    def get_count(self, catalog: str = "events") -> int:
        """Return total number of events in catalog."""
        if catalog != "events":
            raise ValueError(f"Unknown catalog: {catalog}")
        cursor = self._conn.execute("SELECT COUNT(*) FROM events")
        return cursor.fetchone()[0]

    def get_size(self) -> int:
        """Return database size in bytes."""
        cursor = self._conn.execute(
            "SELECT page_count * page_size "
            "FROM pragma_page_count(), pragma_page_size()"
        )
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_backend(self) -> str:
        """Return storage backend type ('memory' or 'disk')."""
        return "memory" if self._is_memory else "disk"

    def get_max_size(self) -> int:
        """Return maximum size limit in bytes."""
        return self._max_size

    def close(self) -> None:
        """Close database connection."""
        self._conn.close()


def validate_dataclass_types(instance) -> list:
    """
    Validate that all fields in a dataclass instance match their type annotations.

    Returns a list of error messages for mismatched fields.
    """
    if not dataclasses.is_dataclass(instance):
        raise TypeError(
            f"Expected a dataclass instance, got {type(instance).__name__}"
        )

    errors = []
    type_hints = typing.get_type_hints(type(instance))

    for field in dataclasses.fields(instance):
        if field.name not in type_hints:
            continue

        expected_type = type_hints[field.name]
        actual_value = getattr(instance, field.name)

        if not _is_instance_of(actual_value, expected_type):
            errors.append(
                f"Field '{field.name}': expected {expected_type}, got {type(actual_value).__name__}"
            )

    return errors


def _is_instance_of(value, type_hint) -> bool:
    """Helper to check type against generic type hints."""
    origin = typing.get_origin(type_hint)

    if origin is None:
        return isinstance(value, type_hint)

    if origin is list:
        if not isinstance(value, list):
            return False
        item_type = (
            typing.get_args(type_hint)[0]
            if typing.get_args(type_hint)
            else object
        )
        return all(isinstance(item, item_type) for item in value)

    if origin is dict:
        if not isinstance(value, dict):
            return False
        args = typing.get_args(type_hint)
        if len(args) >= 2:
            key_type, val_type = args[0], args[1]
            return all(
                isinstance(k, key_type) and isinstance(v, val_type)
                for k, v in value.items()
            )
        return True

    if origin is tuple:
        if not isinstance(value, tuple):
            return False
        args = typing.get_args(type_hint)
        if args:
            if len(args) == 1 and args[0] != ():
                item_type = args[0]
                return all(isinstance(item, item_type) for item in value)
            if len(value) != len(args):
                return False
            return all(isinstance(item, t) for item, t in zip(value, args))
        return True

    if origin is set:
        if not isinstance(value, set):
            return False
        item_type = (
            typing.get_args(type_hint)[0]
            if typing.get_args(type_hint)
            else object
        )
        return all(isinstance(item, item_type) for item in value)

    if origin is typing.Union:
        args = typing.get_args(type_hint)
        return any(_is_instance_of(value, arg) for arg in args)

    return isinstance(value, origin)


def validate_dataclass_types_strict(instance) -> None:
    """
    Validate dataclass field types and raise an exception if any mismatch.
    """
    errors = validate_dataclass_types(instance)
    if errors:
        raise TypeError(
            "Type validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )


## Fingerprint
# Like https://github.com/drk1wi/portspoof and
# (https://www.vicarius.io/vsociety/posts/research-evading-portspoof-solution)
class Fingerprint:
    def __init__(
        self,
    ):
        pass


## JSON-RPC


class JsonRpcServer:
    """
    JSON-RPC 2.0 server using asyncio and standard library only.

    This class handles JSON-RPC protocol logic only. Transport layer
    (socket/network) is handled externally - just call handle_request()
    with incoming JSON data.
    """

    JSON_RPC_VERSION = "2.0"

    def __init__(self, name: str = "__main__"):
        self._name = name
        self._logger = logging.getLogger(f"jsonrpc.server.{name}")
        self._methods: typing.Dict[
            str, typing.Callable[..., typing.Awaitable[typing.Any]]
        ] = {}

    def register_method(self, name: str) -> typing.Callable:
        """Decorator to register a JSON-RPC method handler."""

        def decorator(
            func: typing.Callable[..., typing.Awaitable[typing.Any]],
        ) -> typing.Callable:
            self._methods[name] = func
            return func

        return decorator

    async def handle_request(
        self, data: typing.Union[str, bytes]
    ) -> typing.Optional[typing.Union[typing.Dict, typing.List[typing.Dict]]]:
        """
        Handle incoming JSON-RPC request.

        Args:
            data: Raw JSON string or bytes from transport layer

        Returns:
            Response dict/list to send back, or None for notifications
        """
        try:
            request = json.loads(data)
        except json.JSONDecodeError as e:
            return self._error_response(None, -32700, f"Parse error: {e}")

        if isinstance(request, list):
            return await self._handle_batch(request)
        return await self._handle_single(request)

    async def _handle_single(
        self, request: typing.Any
    ) -> typing.Optional[typing.Dict]:
        """Handle a single JSON-RPC request."""
        if not self._validate_request(request):
            return self._error_response(
                request.get("id") if isinstance(request, dict) else None,
                -32600,
                "Invalid Request",
            )

        method_name = request["method"]
        params = request.get("params", [])
        request_id = request.get("id")
        is_notification = request_id is None

        if method_name not in self._methods:
            return self._error_response(
                request_id, -32601, f"Method not found: {method_name}"
            )

        try:
            handler = self._methods[method_name]
            if isinstance(params, dict):
                result = await handler(**params)
            else:
                result = await handler(*params)

            if is_notification:
                return None

            return self._success_response(request_id, result)

        except Exception as e:
            return self._error_response(request_id, -32000, str(e))

    async def _handle_batch(
        self, requests: typing.List[typing.Dict]
    ) -> typing.Optional[typing.List[typing.Dict]]:
        """Handle a batch of JSON-RPC requests."""
        if len(requests) == 0:
            return None

        responses: typing.List[typing.Dict] = []
        for request in requests:
            response = await self._handle_single(request)
            if response is not None:
                responses.append(response)

        return responses if responses else None

    def _validate_request(self, request: typing.Any) -> bool:
        """Validate JSON-RPC 2.0 request structure."""
        if not isinstance(request, dict):
            return False
        if request.get("jsonrpc") != self.JSON_RPC_VERSION:
            return False
        if "method" not in request or not isinstance(request["method"], str):
            return False
        return True

    def _success_response(
        self, request_id: typing.Any, result: typing.Any
    ) -> typing.Dict:
        """Create a success response."""
        return {
            "jsonrpc": self.JSON_RPC_VERSION,
            "id": request_id,
            "result": result,
        }

    def _error_response(
        self, request_id: typing.Any, code: int, message: str
    ) -> typing.Dict:
        """Create an error response."""
        return {
            "jsonrpc": self.JSON_RPC_VERSION,
            "id": request_id,
            "error": {"code": code, "message": message},
        }

    def get_method_names(self) -> typing.List[str]:
        """Return list of registered method names."""
        return list(self._methods.keys())


class JsonRpcUnixServer(JsonRpcServer):
    """
    JSON-RPC 2.0 server listening on Unix domain socket.

    Extends JsonRpcServer to handle Unix domain socket transport.
    """

    def __init__(self, socket_path: str, name: str = "__main__"):
        super().__init__(name)
        self._socket_path = socket_path
        self._server: typing.Optional[asyncio.Server] = None

    async def start(self) -> None:
        """Start the Unix domain socket server."""
        if os.path.exists(self._socket_path):
            os.remove(self._socket_path)

        self._server = await asyncio.start_unix_server(
            self._handle_client, path=self._socket_path
        )

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle incoming client connection."""
        try:
            data = await reader.read(65536)
            if not data:
                return

            response = await self.handle_request(data)

            if response is not None:
                json_response = json.dumps(response)
                writer.write(json_response.encode("utf-8"))
                await writer.drain()
        except asyncio.TimeoutError as e:
            self._logger.error(
                "[%s] Timeout receiving request: %s", self._name, e
            )
        except OSError as e:
            self._logger.error(
                "[%s] Error receiving request: %s", self._name, e
            )
        except Exception as e:
            self._logger.error("[%s] Error handling client: %s", self._name, e)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def stop(self) -> None:
        """Stop the server and clean up."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        if os.path.exists(self._socket_path):
            os.remove(self._socket_path)

    @property
    def socket_path(self) -> str:
        """Return the Unix socket path."""
        return self._socket_path


class JsonRpcTcpServer(JsonRpcServer):
    """
    JSON-RPC 2.0 server listening on TCP socket.

    Extends JsonRpcServer to handle TCP socket transport.
    """

    def __init__(self, host: str, port: int, name: str = "__main__"):
        super().__init__(name)
        self._host = host
        self._port = port
        self._server: typing.Optional[asyncio.Server] = None

    async def start(self) -> None:
        """Start the TCP socket server."""
        self._server = await asyncio.start_server(
            self._handle_client, host=self._host, port=self._port
        )

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle incoming client connection."""
        try:
            data = await reader.read(65536)
            if not data:
                return

            response = await self.handle_request(data)

            if response is not None:
                json_response = json.dumps(response)
                writer.write(json_response.encode("utf-8"))
                await writer.drain()
        except asyncio.TimeoutError as e:
            self._logger.error(
                "[%s] Timeout receiving request: %s", self._name, e
            )
        except OSError as e:
            self._logger.error(
                "[%s] Error receiving request: %s", self._name, e
            )
        except Exception as e:
            self._logger.error("[%s] Error handling client: %s", self._name, e)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def stop(self) -> None:
        """Stop the server and clean up."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    @property
    def host(self) -> str:
        """Return the host address."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port number."""
        # If using dynamic port (port=0), return the actual assigned port
        if self._port == 0 and self._server is not None:
            sock = self._server.sockets[0]  # type: ignore[attr-defined]
            return sock.getsockname()[1]
        return self._port

    def get_address(self) -> tuple[str, int]:
        """Return the (host, port) address."""
        return (self.host, self.port)


class JsonRpcClient:
    """
    JSON-RPC 2.0 client using standard library only.

    This class handles JSON-RPC protocol logic only. Transport layer
    (socket/network) is handled externally - use make_request() to get
    the JSON payload to send, and parse_response() to handle incoming data.
    """

    JSON_RPC_VERSION = "2.0"

    def __init__(self, name: str = "__main__"):
        self._name = name
        self._logger = logging.getLogger(f"jsonrpc.client.{name}")
        self._pending_requests: typing.Dict[typing.Any, typing.Any] = {}
        self._id_counter = 0

    def _next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    def make_request(
        self,
        method: str,
        params: typing.Optional[typing.Union[list, dict]] = None,
    ) -> str:
        """
        Create a JSON-RPC request payload.

        Args:
            method: Method name to call
            params: Optional positional (list) or keyword (dict) parameters

        Returns:
            JSON string to send to server
        """
        request_id = self._next_id()
        request: typing.Dict[str, typing.Any] = {
            "jsonrpc": self.JSON_RPC_VERSION,
            "method": method,
            "id": request_id,
        }
        if params is not None:
            request["params"] = params

        self._pending_requests[request_id] = {
            "method": method,
            "params": params,
        }
        return json.dumps(request)

    def make_notification(
        self,
        method: str,
        params: typing.Optional[typing.Union[list, dict]] = None,
    ) -> str:
        """
        Create a JSON-RPC notification payload (no response expected).

        Args:
            method: Method name to call
            params: Optional positional (list) or keyword (dict) parameters

        Returns:
            JSON string to send to server
        """
        request: typing.Dict[str, typing.Any] = {
            "jsonrpc": self.JSON_RPC_VERSION,
            "method": method,
        }
        if params is not None:
            request["params"] = params

        return json.dumps(request)

    def make_batch(
        self,
        requests: typing.List[
            typing.Tuple[str, typing.Optional[typing.Union[list, dict]]]
        ],
    ) -> str:
        """
        Create a batch JSON-RPC request.

        Args:
            requests: List of (method, params) tuples

        Returns:
            JSON string to send to server
        """
        batch: typing.List[typing.Dict[str, typing.Any]] = []
        for method, params in requests:
            request: typing.Dict[str, typing.Any] = {
                "jsonrpc": self.JSON_RPC_VERSION,
                "method": method,
                "id": self._next_id(),
            }
            if params is not None:
                request["params"] = params
            batch.append(request)

        for req in batch:
            if "id" in req:
                self._pending_requests[req["id"]] = {
                    "method": req["method"],
                    "params": req.get("params"),
                }

        return json.dumps(batch)

    def parse_response(
        self, data: typing.Union[str, bytes]
    ) -> typing.Union[typing.Dict, typing.List[typing.Dict], None]:
        """
        Parse a JSON-RPC response from the server.

        Args:
            data: Raw JSON string or bytes from server

        Returns:
            Parsed response dict/list, or None for parse errors

        Raises:
            JsonRpcError: If response contains an error
        """
        try:
            response = json.loads(data)
        except json.JSONDecodeError as e:
            raise JsonRpcError(-32700, f"Parse error: {e}")

        if isinstance(response, list):
            results = []
            for resp in response:
                parsed = self._parse_single_response(resp)
                if parsed is not None:
                    results.append(parsed)
            return results if results else None
        else:
            return self._parse_single_response(response)

    def _parse_single_response(
        self, response: typing.Any
    ) -> typing.Optional[typing.Dict]:
        """Parse a single JSON-RPC response."""
        if not isinstance(response, dict):
            raise JsonRpcError(-32600, "Invalid response format")

        if response.get("jsonrpc") != self.JSON_RPC_VERSION:
            raise JsonRpcError(-32600, "Invalid JSON-RPC version")

        if "error" in response:
            request_id = response.get("id")
            if request_id in self._pending_requests:
                del self._pending_requests[request_id]
            error = response["error"]
            raise JsonRpcError(
                error.get("code", -32000),
                error.get("message", "Unknown error"),
                error.get("data"),
            )

        if "result" not in response:
            return None

        request_id = response.get("id")
        if request_id in self._pending_requests:
            del self._pending_requests[request_id]

        return response

    def get_pending_count(self) -> int:
        """Return number of pending requests awaiting responses."""
        return len(self._pending_requests)

    def clear_pending(self) -> None:
        """Clear all pending requests."""
        self._pending_requests.clear()


class JsonRpcError(Exception):
    """Exception raised when a JSON-RPC response contains an error."""

    def __init__(
        self,
        code: int,
        message: str,
        data: typing.Optional[typing.Any] = None,
    ):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"JSON-RPC Error {code}: {message}")

    def to_dict(self) -> typing.Dict:
        """Return error as a dict."""
        error_dict = {"code": self.code, "message": self.message}
        if self.data is not None:
            error_dict["data"] = self.data
        return error_dict


class JsonRpcUnixClient(JsonRpcClient):
    """
    JSON-RPC 2.0 client connecting via Unix domain socket.

    Extends JsonRpcClient to handle Unix domain socket transport.
    Connections are created per-request and closed after response.
    """

    def __init__(self, socket_path: str, name: str = "__main__"):
        super().__init__(name)
        self._socket_path = socket_path

    def call(
        self,
        method: str,
        params: typing.Optional[typing.Union[list, dict]] = None,
    ) -> typing.Any:
        """
        Make a JSON-RPC call and return the result.
        Opens connection, sends request, reads response, closes connection.

        Args:
            method: Method name to call
            params: Optional positional (list) or keyword (dict) parameters

        Returns:
            The result from the server
        """
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self._socket_path)

            request = self.make_request(method, params)
            sock.sendall(request.encode("utf-8"))

            data = sock.recv(65536)
            response = self.parse_response(data)

            if isinstance(response, dict):
                return response.get("result")
            return None
        except socket.timeout as e:
            self._logger.error(
                "[%s] Timeout sending/receiving request: %s", self._name, e
            )
            raise
        except OSError as e:
            self._logger.error(
                "[%s] Error sending/receiving request: %s", self._name, e
            )
            raise
        finally:
            sock.close()

    def notify(
        self,
        method: str,
        params: typing.Optional[typing.Union[list, dict]] = None,
    ) -> None:
        """
        Send a JSON-RPC notification (no response expected).
        Opens connection, sends notification, closes connection.

        Args:
            method: Method name to call
            params: Optional positional (list) or keyword (dict) parameters
        """
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self._socket_path)

            notification = self.make_notification(method, params)
            sock.sendall(notification.encode("utf-8"))
        except socket.timeout as e:
            self._logger.error(
                "[%s] Timeout sending notification: %s", self._name, e
            )
            raise
        except OSError as e:
            self._logger.error(
                "[%s] Error sending notification: %s", self._name, e
            )
            raise
        finally:
            sock.close()

    def call_batch(
        self,
        requests: typing.List[
            typing.Tuple[str, typing.Optional[typing.Union[list, dict]]]
        ],
    ) -> typing.List[typing.Dict]:
        """
        Make a batch JSON-RPC call.
        Opens connection, sends batch, reads response, closes connection.

        Args:
            requests: List of (method, params) tuples

        Returns:
            List of response dicts
        """
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self._socket_path)

            batch = self.make_batch(requests)
            sock.sendall(batch.encode("utf-8"))

            data = sock.recv(65536)
            response = self.parse_response(data)

            if isinstance(response, list):
                return response
            return []
        except socket.timeout as e:
            self._logger.error(
                "[%s] Timeout sending/receiving batch request: %s",
                self._name,
                e,
            )
            raise
        except OSError as e:
            self._logger.error(
                "[%s] Error sending/receiving batch request: %s", self._name, e
            )
            raise
        finally:
            sock.close()

    @property
    def socket_path(self) -> str:
        """Return the Unix socket path."""
        return self._socket_path


class JsonRpcTcpClient(JsonRpcClient):
    """
    JSON-RPC 2.0 client connecting via TCP socket.

    Extends JsonRpcClient to handle TCP socket transport.
    Connections are created per-request and closed after response.
    """

    def __init__(self, host: str, port: int, name: str = "__main__"):
        super().__init__(name)
        self._host = host
        self._port = port

    def call(
        self,
        method: str,
        params: typing.Optional[typing.Union[list, dict]] = None,
    ) -> typing.Any:
        """
        Make a JSON-RPC call and return the result.
        Opens connection, sends request, reads response, closes connection.

        Args:
            method: Method name to call
            params: Optional positional (list) or keyword (dict) parameters

        Returns:
            The result from the server
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self._host, self._port))

            request = self.make_request(method, params)
            sock.sendall(request.encode("utf-8"))

            data = sock.recv(65536)
            response = self.parse_response(data)

            if isinstance(response, dict):
                return response.get("result")
            return None
        except socket.timeout as e:
            self._logger.error(
                "[%s] Timeout sending/receiving request: %s", self._name, e
            )
            raise
        except OSError as e:
            self._logger.error(
                "[%s] Error sending/receiving request: %s", self._name, e
            )
            raise
        finally:
            sock.close()

    def notify(
        self,
        method: str,
        params: typing.Optional[typing.Union[list, dict]] = None,
    ) -> None:
        """
        Send a JSON-RPC notification (no response expected).
        Opens connection, sends notification, closes connection.

        Args:
            method: Method name to call
            params: Optional positional (list) or keyword (dict) parameters
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self._host, self._port))

            notification = self.make_notification(method, params)
            sock.sendall(notification.encode("utf-8"))
        except socket.timeout as e:
            self._logger.error(
                "[%s] Timeout sending notification: %s", self._name, e
            )
            raise
        except OSError as e:
            self._logger.error(
                "[%s] Error sending notification: %s", self._name, e
            )
            raise
        finally:
            sock.close()

    def call_batch(
        self,
        requests: typing.List[
            typing.Tuple[str, typing.Optional[typing.Union[list, dict]]]
        ],
    ) -> typing.List[typing.Dict]:
        """
        Make a batch JSON-RPC call.
        Opens connection, sends batch, reads response, closes connection.

        Args:
            requests: List of (method, params) tuples

        Returns:
            List of response dicts
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self._host, self._port))

            batch = self.make_batch(requests)
            sock.sendall(batch.encode("utf-8"))

            data = sock.recv(65536)
            response = self.parse_response(data)

            if isinstance(response, list):
                return response
            return []
        except socket.timeout as e:
            self._logger.error(
                "[%s] Timeout sending/receiving batch request: %s",
                self._name,
                e,
            )
            raise
        except OSError as e:
            self._logger.error(
                "[%s] Error sending/receiving batch request: %s", self._name, e
            )
            raise
        finally:
            sock.close()

    @property
    def host(self) -> str:
        """Return the host address."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port number."""
        return self._port

    def get_address(self) -> tuple[str, int]:
        """Return the (host, port) address."""
        return (self._host, self._port)


## Event dataclasses


@dataclasses.dataclass
class Event:
    time: float
    ev_type: str


class ConnEventEnum(enum.StrEnum):
    OPEN = "conn_open"
    ERROR = "conn_error"
    CLOSE = "conn_close"
    VALIDATE = "conn_validate"


@dataclasses.dataclass
class ConnEvent(Event):
    tarpit_name: str
    tarpit_pattern: str
    peername: tuple[str, int]
    sockname: tuple[str, int]
    metadata: None | dict = None


class WorkerEventEnum(enum.StrEnum):
    INIT = "worker_init"
    READY = "worker_ready"
    TARPIT_INIT = "worker_tarpit_init"
    TARPIT_READY = "worker_tarpit_ready"


@dataclasses.dataclass
class WorkerEvent(Event):
    tarpit_name: None | str = None
    tarpit_pattern: None | str = None
    metadata: None | dict = None


def _decode_event_from_dict(d: dict):
    ev_type = d["ev_type"]
    if any(ev_type == e for e in ConnEventEnum):
        return ConnEvent(**d)
    elif any(ev_type == e for e in WorkerEventEnum):
        return WorkerEvent(**d)
    else:
        raise Exception("Unknown event type")


class TarpitTracer:
    def trace_conn_event(
        self,
        event: ConnEventEnum,
        tarpit_name: str,
        pattern: str,
        peername,
        sockname,
        metadata,
    ):
        assert event in [m.value for m in ConnEventEnum]

        data = ConnEvent(
            time=time.time(),
            ev_type=event,
            tarpit_name=tarpit_name,
            tarpit_pattern=pattern,
            peername=peername,
            sockname=sockname,
            metadata=metadata,
        )

        sys.stdout.write(
            json.dumps(dataclasses.asdict(data), cls=BytesLiteralEncoder)
            + "\r\n"
        )
        sys.stdout.flush()
        # raise NotImplementedError


_tracer = TarpitTracer()


class TarpitWriter:
    """
    A wrapper around asyncio.StreamWriter that adds configurable speed limiting to data transmission.

    This class allows controlling the rate at which data is sent over the network, useful for tarpit
    implementations that intentionally slow down responses to deter automated attacks.
    """

    async def _write_with_interval(self, data):
        for b in range(0, len(data)):
            await asyncio.sleep(abs(self.rate))
            try:  # Handle Exception, because we are in loop
                self.__writer.write(data[b : b + 1])
                await self.__writer.drain()
            except (ConnectionResetError, BrokenPipeError) as e:
                raise e
                return
        await self.__writer.drain()

    async def _write_normal(self, data):
        self.__writer.write(data)
        await self.__writer.drain()

    async def _write_with_speedlimit(self, data):
        """
        Send data in under a speed limit. Send no more than "rate" bytes per second.
        This function is used when crate BaseTarpit.TarpitWriter with positive "rate" value.
        """
        length = len(data)
        count = length // self.rate
        for b in range(0, count):
            await asyncio.sleep(1)
            try:
                self.__writer.write(data[b * self.rate : (b + 1) * self.rate])
                await self.__writer.drain()
            except (ConnectionResetError, BrokenPipeError) as e:
                raise e
                return
        self.__writer.write(data[(count) * self.rate :])
        await self.__writer.drain()

    def change_rate_limit(self, rate: int):
        # logging.debug(f"rate limit: {rate}")
        self.rate = rate
        if rate == 0:
            write_inner = self._write_normal
        elif rate < 0:
            write_inner = self._write_with_interval
        else:
            write_inner = self._write_with_speedlimit

        self.write_and_drain: typing.Callable[
            [bytes], typing.Awaitable[None]
        ] = write_inner

    def get_extra_info(self, name, default=None):
        return self.__writer.get_extra_info(name, default)

    def close(self):
        return self.__writer.close()

    def wait_closed(self):
        return self.__writer.wait_closed()

    def __init__(self, rate, writer: asyncio.StreamWriter) -> None:
        self.__writer = writer
        self.drain = writer.drain
        # self.close = writer.close
        # self.wait_closed = writer.wait_closed
        # self.write_eof = writer.write_eof
        self.change_rate_limit(rate)


class ReaderProtocol(typing.Protocol):
    async def read(self, n: int = -1) -> bytes:
        raise NotImplementedError


class TarpitReader:
    """
    A wrapper around asyncio.StreamReader designed for client request logging.

    This class intercepts data reads from the underlying StreamReader and buffers
    the initial portion of incoming data up to a configurable length. This allows
    for logging client requests (e.g., protocol headers) without disrupting the
    normal flow of data processing in tarpit handlers.
    """

    def _record_data(self, data: bytes):
        if self._recording_len:
            buffer_len = len(self.__buffer)
            data_len = len(data)
            if buffer_len + data_len < self._recording_len:
                self.__buffer.extend(data)
            elif buffer_len < self._recording_len:
                free_space = self._recording_len - buffer_len
                if data_len <= free_space:
                    self.__buffer.extend(data)
                else:
                    self.__buffer.extend(data[0:free_space])
            else:
                pass

    async def drain_data(self):
        buffer_len = len(self.__buffer)
        if buffer_len < self._recording_len:
            try:
                # This is some kind of tricky
                # Because failed write will cause reader to raise exception
                # See https://github.com/python/cpython/issues/75044
                self.__reader.set_exception(None)  # type: ignore
            except Exception:
                pass
            try:
                self.__buffer.extend(
                    await read_with_timeout(
                        reader=self.__reader,
                        n=self._recording_len - buffer_len,
                        timeout=1,
                    )
                )
            except Exception:
                pass

    def dump_data(self):
        if self._recording_len:
            return self.__buffer
        else:
            return None

    async def read(self, n=-1):
        data = await self.__reader.read(n)
        self._record_data(data)
        return data

    def __init__(
        self, recording_len: int, reader: asyncio.StreamReader
    ) -> None:
        self.__reader = reader
        self.__buffer = bytearray()
        self._recording_len: int = recording_len  # Zero is disable.


async def read_with_timeout(
    reader: ReaderProtocol, n: int, timeout: float
) -> bytes:
    data = bytearray()
    try:
        async with asyncio.timeout(timeout):
            while len(data) < n:
                chunk = await reader.read(n - len(data))
                if not chunk:
                    break
                data.extend(chunk)
    except asyncio.TimeoutError:
        pass
    return bytes(data)


class BaseTarpit:
    """
    This class should not be used directly.
    """

    PATTERN_NAME: str = "_base_tarpit"
    PATTERN_NAME_ALIAS: list[str] = []

    @dataclasses.dataclass
    class RuntimeConfig:
        name: str = "_no_name_defined"
        max_clients: int = 4096
        # Note: max_clients is not real connection count.
        # More than 4096 will be created, but will wait in queue. See:
        # https://docs.python.org/3/library/socket.html#socket.socket.listen
        # default backlog is 100
        rate_limit: int = 8
        trace_level: int = 0
        validation_level: int = 0

        _TRACE_LEVEL_MAP: typing.ClassVar[dict] = {
            "none": 0,
            "access": 1,
            "request": 2,
            0: 0,
            1: 1,
            2: 2,
        }
        _VALIDATION_LEVEL_MAP: typing.ClassVar[dict] = {
            "none": 0,
            "check": 1,
            "true": 2,
            0: 0,
            1: 1,
            2: 2,
        }

        @classmethod
        def from_dict(cls, config_data: dict) -> "BaseTarpit.RuntimeConfig":
            conf = {}
            for key, value in config_data.items():
                if key == "trace_level":
                    conf["trace_level"] = cls._convert_trace_level(value)
                elif key == "validation_level":
                    conf["validation_level"] = cls._convert_validation_level(
                        value
                    )
                elif value is None:
                    pass  # See None as default
                else:
                    conf[key] = value
            # print(cls(**conf), file=sys.stderr)
            return cls(**conf)

        @classmethod
        def _convert_config_value(
            cls, value: str | int, mapping: dict, field_name: str
        ) -> int:
            if isinstance(value, str):
                value = value.lower()
            try:
                return mapping[value]
            except KeyError:
                logging.warning(
                    "invalid %s: %r, using default 0", field_name, value
                )
                return 0

        @classmethod
        def _convert_trace_level(cls, value: str | int) -> int:
            return cls._convert_config_value(
                value, cls._TRACE_LEVEL_MAP, "trace_level"
            )

        @classmethod
        def _convert_validation_level(cls, value: str | int) -> int:
            return cls._convert_config_value(
                value, cls._VALIDATION_LEVEL_MAP, "validation_level"
            )

    def _setup(self):
        """
        Setting up the Tarpit

        Classes that inherit this Class can implement this method
        as an alternative to overloading __init__.
        """

        if hasattr(super(), "_setup"):
            super()._setup()  # type: ignore

        return

    def _trace_client(
        self,
        writer: "asyncio.StreamWriter | TarpitWriter",
        event: ConnEventEnum,
        meta=None,
    ) -> None:
        _tracer.trace_conn_event(
            event=event,
            tarpit_name=self._config.name,
            pattern=self.PATTERN_NAME,
            peername=writer.get_extra_info("peername"),
            sockname=writer.get_extra_info("sockname"),
            metadata=meta,
        )

    async def _handler(
        self,
        reader: TarpitReader,
        writer: TarpitWriter,
    ):
        raise NotImplementedError

    async def __handler_common(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        async with self.sem:
            tarpit_writer: TarpitWriter | None = None
            tarpit_reader: TarpitReader | None = None
            try:
                tarpit_writer = TarpitWriter(
                    128,
                    writer=writer,
                )
                if self._config.trace_level >= 2:
                    reader_background_log = 1024
                else:
                    reader_background_log = 0
                tarpit_reader = TarpitReader(
                    reader_background_log, reader=reader
                )
                self._trace_client(writer, ConnEventEnum.OPEN)
                await self._handler(tarpit_reader, tarpit_writer)
            except (
                BrokenPipeError,
                ConnectionAbortedError,
                ConnectionResetError,
            ) as e:
                self._trace_client(
                    writer,
                    ConnEventEnum.ERROR,
                    meta={"err": e.__class__.__name__, "msg": str(e)},
                )
            except asyncio.exceptions.CancelledError:
                self.logger.debug("task cancelled")
            except OSError as e:
                if hasattr(e, "winerror") and getattr(e, "winerror") == 121:
                    self._trace_client(
                        writer,
                        ConnEventEnum.ERROR,
                        meta={"err": e.__class__.__name__, "msg": str(e)},
                    )
                else:
                    self.logger.exception(e)
            except Exception as e:
                self.logger.exception(e)
            finally:
                recorded_request = (
                    tarpit_reader.dump_data()
                    if tarpit_reader is not None
                    else None
                )
                self._trace_client(
                    writer,
                    ConnEventEnum.CLOSE,
                    meta={"recorded_request": recorded_request},
                )

    async def create_server(self, host, port, start_serving=False):
        """
        Create a TCP server of this Tarpit and listen on the port of host address.

        Returns a asyncio.Server object.

        This function won't start the server immediately.
        The user should await on Server.start_serving() or
        Server.serve_forever() to make the server to start accepting connections.
        """
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        server = await asyncio.start_server(
            self.__handler_common,
            host=host,
            port=port,
            # limit=64,
            # the buffer size of Stream reader, 64 byte
            # by default will be 64 kb, too much since we do not read
            # and the os kernel has it own buffer
            # backlog=100,
        )
        return server

    def __init__(self, **config) -> None:
        """
        Classes that inherit this class SHOULD NOT overload this method.
        **options can be used to pass argument
        """
        self.logger = logging.getLogger(__name__)
        self._config: BaseTarpit.RuntimeConfig = self.RuntimeConfig.from_dict(
            config
        )

        result = validate_dataclass_types(self._config)
        if len(result) > 0:
            self.logger.error(result)
            raise TypeError("Wrong data type in RuntimeConfig")

        self.logger.info(
            "server config: {}".format(self._config),
            dataclasses.asdict(self._config),
        )
        self.sem = asyncio.Semaphore(self._config.max_clients)

        # Call setup for subclass setup
        self._setup()


class StaticTarpit(BaseTarpit):
    """Base class for tarpits with static/client validation support.

    Subclasses should override the validator_* class attributes to configure
    validation behavior. For dynamic values using self, set instance attributes
    in __init__ before calling super().__init__().
    """

    # Validator configuration - override these class attributes in subclasses
    validator_head_allowlist: tuple[bytes, ...] = (b"",)
    validator_timeout: float = 2
    validator_read_len: int = 4
    validator_banner: bytes = b""
    validator_response_failed: bytes = b""

    class ValidationResult(typing.NamedTuple):
        expected: int  # 0 means failed and connection should close, 1 means good/good, 2 means check is skipped
        data: bytes | None = None
        comment: str | None = None

    ValidatorCallable = typing.Callable[
        [TarpitReader, TarpitWriter],
        typing.Awaitable[ValidationResult],
    ]

    _validator_support: int = 0

    async def _validate_client(self, reader, writer):
        await writer.write_and_drain(self.validator_banner)

        # If validation is disabled on validation-enabled tarpit, skip reading/checking client request
        if not self._config.validation_level:
            # Simply send banner but no validation occurs - for compliance when user sets validation_level=0 on supporting tarpits
            return self.ValidationResult(2, None, "validation disabled")

        # For validation enabled: read and validate client data normally
        data = await read_with_timeout(
            reader, self.validator_read_len, self.validator_timeout
        )
        for head in self.validator_head_allowlist:
            if data.startswith(head):
                return self.ValidationResult(1, data)  # 1 means good/valid
        await writer.write_and_drain(self.validator_response_failed)
        return self.ValidationResult(0, data)  # 0 means failed/disconnect

    async def __fake_validate_client(self, reader, writer):
        # For scenarios where validation is enabled but not supported by the tarpit
        # Send banner to maintain protocol compliance, read client data but consider it 'not applicable'
        await writer.write_and_drain(self.validator_banner)
        data = await read_with_timeout(
            reader,
            self.validator_read_len,
            self.validator_timeout,
        )
        return self.ValidationResult(
            2, data, "validation not applicable to this tarpit"
        )  # 2 means validation was turned on but not applicable to this tarpit

    async def __handle_valid_client(self, reader, tarpit_writer):
        tarpit_writer.change_rate_limit(self._config.rate_limit)
        await self.handle_client(tarpit_writer)
        await tarpit_writer.drain()

    async def __drain_remaining_data(self, reader: TarpitReader, writer):
        await reader.read(1024)  # Read and save to buffer
        for _ in range(4):  # 4 second timeout, 1 kb data
            try:
                if await asyncio.wait_for(reader.read(256), 1) == b"":
                    break
            except asyncio.TimeoutError:
                pass

    async def _handler(self, reader, writer):
        tarpit_writer = typing.cast(TarpitWriter, writer)
        tarpit_reader = typing.cast(TarpitReader, reader)

        # Always call validation (which sends banner and reads initial client request)
        result = await self.__runtime_validate_client(
            tarpit_reader, tarpit_writer
        )

        # Trace the validation result
        self._trace_client(
            tarpit_writer, ConnEventEnum.VALIDATE, meta=result._asdict()
        )

        # All validation results now continue with tarpit behavior for protocol compliance,
        # but behavior may differ based on validation outcome

        if result.expected == 0:
            # Validation failed - apply punitive delay, but continue with tarpit behavior
            await asyncio.sleep(random.randrange(16, 32))

            # Continue the tarpit behavior even after validation failure
            # This ensures the service keeps the connection in a tarpit-like state for scanners
            tarpit_writer.change_rate_limit(self._config.rate_limit)
            await asyncio.gather(
                # split read and write. we read and write at the same time.
                # because we cant read after exception is raised.
                self.__handle_valid_client(tarpit_reader, tarpit_writer),
                self.__drain_remaining_data(tarpit_reader, tarpit_writer),
            )
        elif result.expected in (1, 2):
            # Valid request (1) or validation skipped (2) - continue with normal tarpit operation
            tarpit_writer.change_rate_limit(self._config.rate_limit)

            # Handle normal tarpit operations
            await asyncio.gather(
                # split read and write. we read and write at the same time.
                self.__handle_valid_client(tarpit_reader, tarpit_writer),
                self.__drain_remaining_data(tarpit_reader, tarpit_writer),
            )
        # Other unexpected codes will continue with the default path as well for robustness

        tarpit_writer.close()
        await tarpit_writer.wait_closed()

    def __init__(self, **config):
        super().__init__(**config)

        self.__runtime_validate_client: StaticTarpit.ValidatorCallable
        # setup client_validation
        if not self._config.validation_level:
            self.logger.debug("client_validation disabled")
            # Use main validation method which will bypass validation internally when disabled
            self.__runtime_validate_client = self._validate_client
        elif self._validator_support == 1:
            self.logger.debug("client_validation enabled")
            # Use main validation method for validation-enabled tarpits
            self.__runtime_validate_client = self._validate_client
        else:
            # Use special method for tarpits that don't support validation
            self.__runtime_validate_client = self.__fake_validate_client
            self.logger.warning(
                "this tarpit does not support client_validation"
            )

    async def handle_client(self, writer):
        pass


class DynamicTarpit(BaseTarpit):
    async def _handler(self, reader, writer):
        tarpit_writer = typing.cast(TarpitWriter, writer)
        tarpit_reader = typing.cast(TarpitReader, reader)
        tarpit_writer.rate
        return self.handle_client(tarpit_reader, tarpit_writer)

    async def handle_client(self, reader, writer):
        raise NotImplementedError

    def __init__(self, **config):
        super().__init__(**config)

        if self._config.validation_level:
            self.logger.warning(
                "this tarpit does not support client_validation"
            )


class EchoTarpit(DynamicTarpit):
    PATTERN_NAME: str = "_internal_echo"

    async def handle_client(self, reader, writer: TarpitWriter):
        """
        Callback for providing service

        And this method is an example of echo server.
        """
        print()
        print("This is a test 'echo' service!")
        data = await reader.read(100)
        message = data.decode()
        print(f"Sending: {message!r}")
        await writer.write_and_drain(data)
        await writer.drain()
        print("Close the connection")
        # writer.close()
        # await writer.wait_closed()


class EndlessBannerTarpit(StaticTarpit):
    PATTERN_NAME: str = "endless_banner"

    async def handle_client(self, writer: TarpitWriter):
        while True:
            await writer.write_and_drain(b"%x\r\n" % random.randint(0, 2**32))


class EgshAminoasTarpit(StaticTarpit):
    PATTERN_NAME: str = "egsh_aminoas"
    # cSpell:disable
    # These is a joke
    # https://github.com/HanaYabuki/aminoac
    AMINOCESE_DICT = {
        "Egsh Aminoas": "en:Song of Aminoas",
        "Aminoas": "en:Aminoas",
        "Ama Cinoas": "en:my beautiful homeland",
        "Yegm Laminoas": "en:no matter when, my heart yearns for you",
    }

    _aminocese_cache: list = []

    # cSpell:enable
    async def handle_client(self, writer: TarpitWriter):
        while True:
            a = random.choice(self._aminocese_cache)
            header = a.encode() + b"\r\n"
            await writer.write_and_drain(header)
            self.logger.info(a)

    def _setup(self):
        self._aminocese_cache = list(self.AMINOCESE_DICT.keys())


#
# HTTP
#


class HttpTarpit(StaticTarpit):
    _validator_support = 1
    validator_head_allowlist: tuple[bytes, ...] = (b"GET ", b"HEAD")

    class Connection:
        writer: TarpitWriter
        send_raw: typing.Callable[[bytes | bytearray], typing.Awaitable[None]]

        @staticmethod
        def to_bytes(data) -> bytes:
            t = type(data)
            if t is bytearray:
                return data
            elif t is bytes:
                return data
            elif t is str:
                return bytes(data, "ASCII")
            else:
                return bytes(data)

        async def send_status_line(
            self, code: int, version: bytes = b"HTTP/1.1"
        ):
            status = http.HTTPStatus(code)
            await self.writer.write_and_drain(
                b"%s %d %s\r\n"
                % (version, status, bytes(status.phrase, "ASCII"))
            )
            await self.send_raw(
                b"Server: Apache/2.4.9\r\nX-Powered-By: PHP/5.1.2-1+b1\r\n"
            )
            # Note: There should be a Date header
            #       But we just omit it
            # https://www.rfc-editor.org/rfc/rfc9110.html
            # An origin server with a clock (as defined in Section 5.6.7) MUST
            # generate a Date header field in all 2xx (Successful),
            # 3xx (Redirection), and 4xx (Client Error) responses,
            # and MAY generate a Date header
            # field in 1xx (Informational) and 5xx (Server Error) responses.

        async def send_header(self, keyword: bytes, value: bytes):
            await self.writer.write_and_drain(b"%s: %s\r\n" % (keyword, value))

        async def end_headers(self):
            await self.writer.write_and_drain(b"\r\n")

        async def send_content(
            self,
            content: bytes | bytearray,
            type_: bytes = b"",
            encoding: bytes = b"",
        ):
            if len(type_):
                await self.send_header(b"Content-Type", type_)
            else:
                await self.send_header(
                    b"Content-Type", b"text/html; charset=UTF-8"
                )

            await self.send_header(b"Content-Length", b"%d" % len(content))
            if len(encoding):
                await self.send_header(b"Content-Encoding", encoding)
            await self.end_headers()
            await self.send_raw(content)

        def __init__(self, writer: TarpitWriter) -> None:
            self.writer = writer
            self.send_raw: typing.Callable[
                [bytes | bytearray], typing.Awaitable[None]
            ] = typing.cast(
                typing.Callable[[bytes | bytearray], typing.Awaitable[None]],
                writer.write_and_drain,
            )

    async def _http_handler(self, connection: Connection):
        pass

    async def handle_client(self, writer: TarpitWriter):
        conn: HttpTarpit.Connection = HttpTarpit.Connection(writer)
        await self._http_handler(conn)


class HttpOkTarpit(HttpTarpit):
    PATTERN_NAME: str = "_internal_http_ok"

    async def _http_handler(self, connection):
        await connection.send_status_line(200)
        await connection.send_content(b"DUCK!")
        # Left close to wrapped handler
        # await connection.close()


class HttpFakeAuthTarpit(HttpTarpit):
    PATTERN_NAME: str = "http_fake_auth"

    async def _http_handler(self, connection):
        await connection.send_status_line(401)
        await connection.send_header(
            b"WWW-Authenticate", b'Basic realm="Server"'
        )
        await connection.send_content(b"401 Unauthorized")


class HttpEndlessHeaderTarpit(HttpTarpit):
    PATTERN_NAME: str = "http_endless_header"

    async def _http_handler(self, connection):
        await connection.send_status_line(200)
        while True:
            header = b"Set-Cookie: "
            await connection.send_raw(header)
            header = b"%x=%x\r\n" % (
                random.randint(0, 2**32),
                random.randint(0, 2**32),
            )
            await connection.send_raw(header)


class HttpPreGeneratedTarpit(HttpTarpit):
    @dataclasses.dataclass
    class RuntimeConfig(HttpTarpit.RuntimeConfig):
        rate_limit: int = 128

    class Content(typing.NamedTuple):
        data: bytes | bytearray
        type_: str = ""
        encoding: str = ""

    async def _http_handler(self, connection: HttpTarpit.Connection):
        await connection.send_status_line(200)
        await connection.send_content(
            content=self._content_generated.data,
            type_=self._content_generated.type_.encode("ASCII"),
            encoding=self._content_generated.encoding.encode("ASCII"),
        )

    def _setup(self):
        super()._setup()
        self._content_generated = self._generate_content()

    def _generate_content(self) -> Content:
        """
        Subclass should overload this method
        """
        raise NotImplementedError


class HttpBadHtmlTarpit(HttpPreGeneratedTarpit):
    PATTERN_NAME = "http_bad_site"
    # const WORKERS = 4, SAMPLES_PER = 1e10;
    # const wSrc = `
    # self.onmessage = e => {
    # const n = e.data;
    # let hit=0;
    # for(let i=0;i<n;i++){
    #     const x=Math.random(), y=Math.random();
    #     if(x*x+y*y<=1) hit++;
    # }
    # postMessage(hit);
    # close();
    # };`;
    # const blob = new Blob([wSrc],{type:'application/javascript'});
    # const url = URL.createObjectURL(blob);
    # let remaining = WORKERS, totalHit = 0, totalSamples = WORKERS*SAMPLES_PER;
    # for(let i=0;i<WORKERS;i++){
    # const w = new Worker(url);
    # w.onmessage = e => {
    #     totalHit += e.data;
    #     remaining--;
    #     if(remaining===0){
    #     console.log('pi ~=', (4*totalHit/totalSamples));
    #     URL.revokeObjectURL(url);
    #     }
    # };
    # w.postMessage(SAMPLES_PER);
    # }
    _BAD_SCRIPT = (
        b"const _0x703edb=0x4,_0x123279=0x2540be400,_0x367ad8='\\x73\\x65\\x6c\\x66\\x2e\\x6f\\x6"
        b"e\\x6d\\x65\\x73\\x73\\x61\\x67\\x65\\x3d\\x73\\x3d\\x3e\\x7b\\x63\\x6f\\x6e\\x73\\x74\\x20\\x61\\x3"
        b"d\\x73\\x2e\\x64\\x61\\x74\\x61\\x3b\\x6c\\x65\\x74\\x20\\x65\\x3d\\x30\\x3b\\x66\\x6f\\x72\\x28\\x6"
        b"c\\x65\\x74\\x20\\x73\\x3d\\x30\\x3b\\x73\\x3c\\x61\\x3b\\x73\\x2b\\x2b\\x29\\x7b\\x63\\x6f\\x6e\\x7"
        b"3\\x74\\x20\\x73\\x3d\\x4d\\x61\\x74\\x68\\x2e\\x72\\x61\\x6e\\x64\\x6f\\x6d\\x28\\x29\\x2c\\x61\\x3"
        b"d\\x4d\\x61\\x74\\x68\\x2e\\x72\\x61\\x6e\\x64\\x6f\\x6d\\x28\\x29\\x3b\\x73\\x2a\\x73\\x2b\\x61\\x2"
        b"a\\x61\\x3c\\x3d\\x31\\x26\\x26\\x65\\x2b\\x2b\\x7d\\x70\\x6f\\x73\\x74\\x4d\\x65\\x73\\x73\\x61\\x6"
        b"7\\x65\\x28\\x65\\x29\\x2c\\x63\\x6c\\x6f\\x73\\x65\\x28\\x29\\x7d\\x3b',_0x1ef293=new Blob([_"
        b"0x367ad8],{'\\x74\\x79\\x70\\x65':'\\x61\\x70\\x70\\x6c\\x69\\x63\\x61\\x74\\x69\\x6f\\x6e\\x2f\\"
        b"x6a\\x61\\x76\\x61\\x73\\x63\\x72\\x69\\x70\\x74'}),_0x5a3005=URL['\\x63\\x72\\x65\\x61\\x74\\x"
        b"65\\x4f\\x62\\x6a\\x65\\x63\\x74\\x55\\x52\\x4c'](_0x1ef293);let _0x1e2891=_0x703edb,_0x4"
        b"9416f=0x0,_0x23ba9f=_0x703edb*_0x123279;for(let _0x1dccc8=0x0;_0x1dccc8<_0x703ed"
        b"b;_0x1dccc8++){const _0x4b0c4f=new Worker(_0x5a3005);_0x4b0c4f['\\x6f\\x6e\\x6d\\x65"
        b"\\x73\\x73\\x61\\x67\\x65']=_0xdafd07=>{_0x49416f+=_0xdafd07['\\x64\\x61\\x74\\x61'],_0x1"
        b"e2891--,_0x1e2891===0x0&&(console['\\x6c\\x6f\\x67']('\\x70\\x69\\x20\\x7e\\x3d',0x4*_0x"
        b"49416f/_0x23ba9f),URL['\\x72\\x65\\x76\\x6f\\x6b\\x65\\x4f\\x62\\x6a\\x65\\x63\\x74\\x55\\x52\\"
        b"x4c'](_0x5a3005));},_0x4b0c4f['\\x70\\x6f\\x73\\x74\\x4d\\x65\\x73\\x73\\x61\\x67\\x65'](_0"
        b"x123279);}"
    )

    def _generate_content(self):
        data = bytearray()

        data.extend(
            b"<!DOCTYPE html><html><body><script>%s</script>"
            % (self._BAD_SCRIPT)
        )

        for i in range(300):
            data.extend(
                b"<div id='%x'>SUPER<a href='/%x.html'>HOT</a>"
                % (random.randint(0, 2**32), random.randint(0, 2**32))
            )
        for i in range(300):
            data.extend(b"</div>")

        self.logger.debug("generated bad html %i kb", len(data) / 1024)
        return self.Content(data)


class HttpDeflateTarpit(HttpPreGeneratedTarpit):
    @dataclasses.dataclass
    class RuntimeConfig(HttpPreGeneratedTarpit.RuntimeConfig):
        rate_limit: int = 16
        compression_type: str = "gzip"

    def _make_deflate(self, compressobj):
        raise NotImplementedError

    def _generate_content(self):
        self._deflate_content = b""
        self.compression_type = typing.cast(
            str, getattr(self._config, "compression_type", "gzip")
        )
        match self.compression_type:
            case "gzip":
                compressobj = zlib.compressobj(level=9, wbits=31)
            case "deflate":
                compressobj = zlib.compressobj(level=9, wbits=15)
            case _:
                compressobj = zlib.compressobj(level=9, wbits=31)
        if compressobj is None:
            compressobj = zlib.compressobj(level=9, wbits=31)
        self._make_deflate(compressobj)
        return self.Content(
            data=self._deflate_content, encoding=self.compression_type
        )


class HttpDeflateSizeBombTarpit(HttpDeflateTarpit):
    PATTERN_NAME: str = "http_deflate_size_bomb"

    @dataclasses.dataclass
    class RuntimeConfig(HttpDeflateTarpit.RuntimeConfig):
        rate_limit: int = 16
        compression_type: str = "deflate"

    def _make_deflate(self, compressobj):
        t = compressobj
        bomb = bytearray()
        bomb.extend(t.compress(b"<html>MORE!</dd>" * 5))
        # The Maximum Compression Factor of zlib is about 1000:1
        # so 1024**2 means 1 MB original data, 1 KB after compression
        # According to https://www.zlib.net/zlib_tech.html
        for _ in range(0, 1000):
            bomb.extend(t.compress(bytes(1024**2)))
        bomb.extend(t.compress(b"</html>MORE!</dd>" * 5))
        bomb.extend(t.flush())
        self._deflate_content = bomb
        self.logger.info(f"deflate bomb created:{int(len(bomb) / 1024):d}kb")


class HttpDeflateHtmlBombTarpit(HttpDeflateTarpit):
    PATTERN_NAME: str = "http_deflate_html_bomb"

    def _make_deflate(self, compressobj):
        self.logger.info("creating bomb...")
        t = compressobj
        bomb = bytearray()
        # To successfully make Firefox and Chrome stuck, only zeroes is not enough
        # Chromium needs 2.1 GB of memory during displaying this page, and SIGSEGV finally.
        # about 8MB uncompressed, 20 kb compressed
        bomb.extend(t.compress(b"<!DOCTYPE html><html><body>"))
        bomb.extend(t.compress(b"<div>COOL</dd>" * 102400))
        bomb.extend(t.compress(b"<div>SUPER</a><em>HOT</em></span>" * 102400))
        bomb.extend(
            t.compress(
                b'<table></div><a>SUPER<tr><td rowspan="201" colspan="1">HOT</dd>'
                * 51200
            )
        )
        bomb.extend(t.compress(b"<table>MORE!</dd>" * 5))
        bomb.extend(t.flush())
        self._deflate_content = bomb
        self.logger.info(f"deflate bomb created:{int(len(bomb) / 1024):d} kb")


#
# SSH
#


class SshTarpit(StaticTarpit):
    SSH_VERSION_STRING = b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.3\r\n"
    # pretend to be ubuntu
    # see: https://svn.nmap.org/nmap/nmap-service-probes

    _validator_support = 1
    validator_head_allowlist: tuple[bytes, ...] = (b"SSH-",)
    validator_response_failed = SSH_VERSION_STRING

    class SshMegNumber(enum.IntEnum):
        """
        RFC 4250 4.1

        The Message Number is a byte value that describes the payload of a
        packet.
        """

        SSH_MSG_IGNORE = 2
        SSH_MSG_UNIMPLEMENTED = 3
        SSH_MSG_DEBUG = 4

    @classmethod
    def make_ssh_packet(cls, payload):
        packet = bytearray()
        total_length = 4 + 1 + len(payload)
        padding = 16 - (total_length % 8)
        packet += (total_length - 4 + padding).to_bytes(4, "big")
        packet += padding.to_bytes(1, "big")
        packet += payload
        packet += bytes(padding)
        return packet

    @classmethod
    def make_ssh_msg(cls, type: int, data):
        msg = bytearray(type.to_bytes(1, "big"))
        msg += data
        return msg

    @classmethod
    def make_ssh_msg_ignore(cls, length):
        return cls.make_ssh_msg(cls.SshMegNumber.SSH_MSG_IGNORE, bytes(length))


class SshTransHoldTarpit(SshTarpit):
    PATTERN_NAME: str = "ssh_trans_hold"

    @property
    def OPENSSH_KEX(self):
        """
        Hard-coded Key Exchange Init message
        from a OpenSSH 9.5 client.

        It can be used in server,
        because server and client uses the same format.
        """
        return bytes.fromhex(
            "1417a3abdb8fa4d9ba63aea67651cbc85b00000114736e747275703736317832"
            "353531392d736861353132406f70656e7373682e636f6d2c6375727665323535"
            "31392d7368613235362c637572766532353531392d736861323536406c696273"
            "73682e6f72672c656364682d736861322d6e697374703235362c656364682d73"
            "6861322d6e697374703338342c656364682d736861322d6e697374703532312c"
            "6469666669652d68656c6c6d616e2d67726f75702d65786368616e67652d7368"
            "613235362c6469666669652d68656c6c6d616e2d67726f757031362d73686135"
            "31322c6469666669652d68656c6c6d616e2d67726f757031382d736861353132"
            "2c6469666669652d68656c6c6d616e2d67726f757031342d7368613235362c65"
            "78742d696e666f2d63000001cf7373682d656432353531392d636572742d7630"
            "31406f70656e7373682e636f6d2c65636473612d736861322d6e697374703235"
            "362d636572742d763031406f70656e7373682e636f6d2c65636473612d736861"
            "322d6e697374703338342d636572742d763031406f70656e7373682e636f6d2c"
            "65636473612d736861322d6e697374703532312d636572742d763031406f7065"
            "6e7373682e636f6d2c736b2d7373682d656432353531392d636572742d763031"
            "406f70656e7373682e636f6d2c736b2d65636473612d736861322d6e69737470"
            "3235362d636572742d763031406f70656e7373682e636f6d2c7273612d736861"
            "322d3531322d636572742d763031406f70656e7373682e636f6d2c7273612d73"
            "6861322d3235362d636572742d763031406f70656e7373682e636f6d2c737368"
            "2d656432353531392c65636473612d736861322d6e697374703235362c656364"
            "73612d736861322d6e697374703338342c65636473612d736861322d6e697374"
            "703532312c736b2d7373682d65643235353139406f70656e7373682e636f6d2c"
            "736b2d65636473612d736861322d6e69737470323536406f70656e7373682e63"
            "6f6d2c7273612d736861322d3531322c7273612d736861322d3235360000006c"
            "63686163686132302d706f6c7931333035406f70656e7373682e636f6d2c6165"
            "733132382d6374722c6165733139322d6374722c6165733235362d6374722c61"
            "65733132382d67636d406f70656e7373682e636f6d2c6165733235362d67636d"
            "406f70656e7373682e636f6d0000006c63686163686132302d706f6c79313330"
            "35406f70656e7373682e636f6d2c6165733132382d6374722c6165733139322d"
            "6374722c6165733235362d6374722c6165733132382d67636d406f70656e7373"
            "682e636f6d2c6165733235362d67636d406f70656e7373682e636f6d000000d5"
            "756d61632d36342d65746d406f70656e7373682e636f6d2c756d61632d313238"
            "2d65746d406f70656e7373682e636f6d2c686d61632d736861322d3235362d65"
            "746d406f70656e7373682e636f6d2c686d61632d736861322d3531322d65746d"
            "406f70656e7373682e636f6d2c686d61632d736861312d65746d406f70656e73"
            "73682e636f6d2c756d61632d3634406f70656e7373682e636f6d2c756d61632d"
            "313238406f70656e7373682e636f6d2c686d61632d736861322d3235362c686d"
            "61632d736861322d3531322c686d61632d73686131000000d5756d61632d3634"
            "2d65746d406f70656e7373682e636f6d2c756d61632d3132382d65746d406f70"
            "656e7373682e636f6d2c686d61632d736861322d3235362d65746d406f70656e"
            "7373682e636f6d2c686d61632d736861322d3531322d65746d406f70656e7373"
            "682e636f6d2c686d61632d736861312d65746d406f70656e7373682e636f6d2c"
            "756d61632d3634406f70656e7373682e636f6d2c756d61632d313238406f7065"
            "6e7373682e636f6d2c686d61632d736861322d3235362c686d61632d73686132"
            "2d3531322c686d61632d736861310000001a6e6f6e652c7a6c6962406f70656e"
            "7373682e636f6d2c7a6c69620000001a6e6f6e652c7a6c6962406f70656e7373"
            "682e636f6d2c7a6c696200000000000000000000000000"
        )

    async def handle_client(self, writer: TarpitWriter):
        # later_rate = writer.rate
        # if writer.rate < 128:
        # Change to a faster rate to send the KEX handshake
        # writer.change_rate_limit(128)

        # Send identifier
        # RFC 4253:
        # Key exchange will begin immediately after sending this identifier.
        await writer.write_and_drain(self.SSH_VERSION_STRING)
        # Send a hard-coded key-exchange message
        payload = self.OPENSSH_KEX
        packet = self.make_ssh_packet(payload)
        await writer.write_and_drain(packet)

        # RFC 4253:
        # Once a party has sent a SSH_MSG_KEXINIT message for key exchange or
        # re-exchange, until it has sent a SSH_MSG_NEWKEYS message (Section
        # 7.3), it MUST NOT send any messages other than:
        # * Transport layer generic messages (1 to 19) (but
        #   SSH_MSG_SERVICE_REQUEST and SSH_MSG_SERVICE_ACCEPT MUST NOT be
        #   sent);
        while True:
            # writer.change_rate_limit(later_rate)
            # SSH_MSG_IGNORE is allowed,
            # so keep sending this will keep connection open
            packet = self.make_ssh_packet(self.make_ssh_msg_ignore(16))
            await writer.write_and_drain(packet)


class SshEndlessTarpit(SshTarpit):
    PATTERN_NAME: str = "ssh_endless_banner"
    PATTERN_NAME_ALIAS: list[str] = ["endlessh"]

    async def handle_client(self, writer: TarpitWriter):
        while True:
            await writer.write_and_drain(b"%x\r\n" % random.randint(0, 2**32))


class TlsTarpit(StaticTarpit):
    PROTOCOL_VERSION_MAGIC = b"\x03\x03"  # TLS 1.2, also apply to 1.3

    _validator_support = 1
    validator_head_allowlist: tuple[bytes, ...] = (b"\x16\x03",)

    # See: TLS 1.2 RFC ttps://www.rfc-editor.org/rfc/rfc5246#page-15
    class TlsRecordContentType(enum.IntEnum):
        HANDSHAKE = 22

    @classmethod
    def make_record(
        cls, content_type: TlsRecordContentType, fragment_data: bytes
    ) -> bytes:
        rec = (
            content_type.to_bytes(1, "big")
            + cls.PROTOCOL_VERSION_MAGIC
            + len(fragment_data).to_bytes(2, "big")
            + fragment_data
        )
        return rec

    class TlsHandshakeType(enum.IntEnum):
        HELLO_REQUEST = 0
        SERVER_HELLO = 2

    @classmethod
    def make_handshake_frag(
        cls, handshake_type: TlsHandshakeType, body: bytes
    ) -> bytes:
        frag = (
            handshake_type.to_bytes(1, "big")
            + len(body).to_bytes(3, "big")
            + body
        )
        return frag


class TlsHelloRequestTarpit(TlsTarpit):
    PATTERN_NAME: str = "tls_endless_hello_request"

    # RFC 5246:
    #
    # The HelloRequest message MAY be sent by the server at any time.
    #
    # HelloRequest is a simple notification that the client should begin
    # the negotiation process anew.  In response, the client should send
    # a ClientHello message when convenient.
    #
    # Servers SHOULD NOT send a
    # HelloRequest immediately upon the client's initial connection.  It
    # is the client's job to send a ClientHello at that time.
    #
    # This message will be ignored by the client if the client is
    # currently negotiating a session.
    @classmethod
    def make_hello_request_record(cls) -> bytes:
        h = cls.make_handshake_frag(cls.TlsHandshakeType.HELLO_REQUEST, b"")
        return cls.make_record(cls.TlsRecordContentType.HANDSHAKE, h)

    async def handle_client(self, writer: TarpitWriter):
        while True:
            packet = self.make_hello_request_record()
            await writer.write_and_drain(packet)


class TlsSlowHelloTarpit(TlsTarpit):
    PATTERN_NAME: str = "tls_slow_hello"

    @classmethod
    def make_server_hello_record(cls) -> bytes:
        padding_data_length = 2**14 - 1024
        session_ticket_data_length = 512
        session_id_length = 32  # Session ID 32 max

        renego_info_ext = b"\xff\x01\x00\x01\x00"
        # 5 bytes
        ec_points_ext = b"\x00\x0b\x00\x02\x01\x00"
        # 6 bytes (type=0x0b, len=2, data=01 00)
        ems_ext = b"\x00\x17\x00\x00"
        # 4 bytes (type=0x17, len=0)

        ticket_data = b"\x00" * session_ticket_data_length
        ticket_ext_len = session_ticket_data_length.to_bytes(2, "big")
        ticket_ext = b"\x00\x23" + ticket_ext_len + ticket_data  # 4 + len

        # Padding Extension (Type 0x0015)
        padding_data = b"\x00" * padding_data_length
        padding_ext_len = padding_data_length.to_bytes(2, "big")
        padding_ext = b"\x00\x15" + padding_ext_len + padding_data  # 4 + len

        extensions_data = (
            renego_info_ext + ec_points_ext + ems_ext + ticket_ext + padding_ext
        )
        extensions_total_len = len(extensions_data).to_bytes(
            2, "big"
        )  # 2 bytes for Extensions Length field

        server_version = b"\x03\x03"  # TLS 1.2
        random_bytes = b"\x00" * 32  # 32 bytes Random
        session_id_len_byte = bytes([32])
        session_id_value = (
            b"\x11" * session_id_length
        )  # Session ID Value (max 32 bytes)
        cipher_suite = (
            b"\xc0\x2f"  # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 (example)
        )
        compression_method = b"\x00"  # Null compression

        handshake_content = (
            server_version
            + random_bytes
            + session_id_len_byte
            + session_id_value
            + cipher_suite
            + compression_method
            + extensions_total_len  # The Extensions Length field
            + extensions_data  # The actual extensions data
        )

        h = cls.make_handshake_frag(
            cls.TlsHandshakeType.SERVER_HELLO, handshake_content
        )
        return cls.make_record(cls.TlsRecordContentType.HANDSHAKE, h)

    async def handle_client(self, writer: TarpitWriter):
        while True:
            await writer.write_and_drain(self._packet)

    def _setup(self):
        super()._setup()
        self._packet = self.make_server_hello_record()


class FtpTarpit(StaticTarpit):
    # https://www.rfc-editor.org/rfc/rfc959
    _validator_support = 1
    validator_banner: bytes = (
        b"220 (vsFTPd 3.0.5)\r\n"
        # b"220 FileZilla Server 1.10.1\r\n"
        # b"220 Please visit https://filezilla-project.org/\r\n"
    )
    validator_head_allowlist: tuple[bytes, ...] = (b"USER",)
    validator_response_failed: bytes = b"530 Please login with USER.\r\n"


class FtpEndlessMotdTarpit(FtpTarpit):
    PATTERN_NAME: str = "ftp_endless_motd"

    async def handle_client(self, writer: TarpitWriter):
        await writer.write_and_drain(b"230-NOTICE: \r\n")
        while True:
            await writer.write_and_drain(
                b"230-%x\r\n" % random.randint(0, 2**32)
            )


class SmtpTarpit(StaticTarpit):
    # https://datatracker.ietf.org/doc/html/rfc5321#appendix-D.1

    _validator_support = 1
    validator_banner: bytes = (
        b"220 [127.0.0.1] ESMTP Sendmail 8.16.1/8.16.1; "
        b"Thu, 01 Sep 1993 00:00:00 +0000\r\n"
    )
    validator_head_allowlist: tuple[bytes, ...] = (b"EHLO", b"HELO")
    validator_response_failed: bytes = (
        b"502 Error: command not implemented.\r\n"
    )


class SmtpEndlessEhloTarpit(SmtpTarpit):
    PATTERN_NAME: str = "smtp_endless_ehlo"

    async def handle_client(self, writer: TarpitWriter):
        await writer.write_and_drain(
            b"250-[127.0.0.1] Hello [192.168.1.1], pleased to meet you \r\n"
        )
        while True:
            await writer.write_and_drain(
                b"250-%x\r\n" % random.randint(0, 2**32)
            )


##
#  Worker and CLI
##


def clean_privilege() -> None:
    # Clean env
    os.environ.clear()
    if os.name == "posix":
        if os.getuid() == 0:
            logging.info("privileged uid detected, dropping privilege")
            # Using a blank uid is not safe,
            # Chroot to /tmp is not safe
            # but still better than running as root
            try:
                os.chroot("/tmp")
                os.chdir("/")
                id_num = 65533
                os.setgroups([id_num])
                os.setresgid(id_num, id_num, id_num)
                os.setresuid(id_num, id_num, id_num)
            except Exception as e:
                logging.warning(f"failed to drop privilege, error: `{e}`")


def generate_conf_from_cli(args, old_config: dict = {}):
    config: dict = {"tarpits": {}, "logging": {}}
    number = 0

    for i in args.pattern:
        pattern = i.casefold().partition(":")[0]
        bind = i.casefold().partition(":")[2]
        host = bind.rpartition(":")[0]
        port = bind.rpartition(":")[2]
        if host.startswith("["):
            host = host[1:-1]
        config["tarpits"][f"cli_{number}"] = {
            "pattern": pattern,
            "rate_limit": args.rate_limit,
            "bind": [{"host": host, "port": port}],
            "validation_level": args.validate_client,
            "trace_level": args.trace,
        }
        number += 1

    if not args.verbose:
        args.verbose = 0
        # logger.setLevel(logging.WARNING)
        config["logging"]["level"] = "warning"
        config["logging"]["fmt"] = "[%(levelname)-8s] %(message)s"
    if args.verbose >= 1:
        config["logging"]["level"] = "info"
    if args.verbose >= 2:
        config["logging"]["level"] = "debug"
        config["logging"]["fmt"] = (
            "[%(levelname)-8s - %(asctime)s] [%(name)s - %(funcName)s] %(message)s"
        )
    if args.verbose >= 3:
        logging.error("higher verbose level is not implemented")

    return config


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def dict_deep_update(
    dest: typing.Dict[str, typing.Any],
    src: typing.Dict[str, typing.Any],
    *,
    list_strategy: str = "replace",  # "replace" or "extend"
    copy_dest: bool = False,
    allow_types: typing.Optional[typing.Iterable[type]] = None,
) -> typing.Dict[str, typing.Any]:
    """
    Deeply update `dest` with `src`.
    - list_strategy: "replace" (src list overwrites) or "extend" (append items from src)
    - copy_dest: if True, operate on a deep copy of dest and return it; otherwise modify dest in-place.
    - allow_types: optional iterable of types that are allowed to be merged; if None, no extra restriction.
    """
    if list_strategy not in ("replace", "extend"):
        raise ValueError("list_strategy must be 'replace' or 'extend'")

    allowed = set(allow_types) if allow_types is not None else None

    target = copy.deepcopy(dest) if copy_dest else dest

    def _merge(a: typing.Any, b: typing.Any):
        # a is existing value in target, b is source value to merge
        # Return merged value (and mutate a in-place when appropriate)
        if isinstance(b, dict) and isinstance(a, dict):
            for k, v in b.items():
                if k in a:
                    a[k] = _merge(a[k], v)
                else:
                    a[k] = copy.deepcopy(v)
            return a

        if isinstance(b, list) and isinstance(a, list):
            if list_strategy == "replace":
                return copy.deepcopy(b)
            else:  # extend
                a.extend(copy.deepcopy(b))
                return a

        if allowed is not None:
            if not any(isinstance(b, t) for t in allowed):
                return copy.deepcopy(b)

        return copy.deepcopy(b)

    for key, val in src.items():
        if key in target:
            target[key] = _merge(target[key], val)
        else:
            target[key] = copy.deepcopy(val)

    return target


def get_log_level(level_in_conf: str):
    return get_case_insensitive_value(
        level_in_conf,
        {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        },
    )


def get_log_handler(file_name_in_conf):
    match file_name_in_conf:
        case "<stdout>":
            return logging.StreamHandler(sys.stdout)
        case "<stderr>":
            return logging.StreamHandler(sys.stderr)
        case _:
            return logging.FileHandler(file_name_in_conf)


def get_case_insensitive_value(key: str, dictionary: dict):
    if not all(ord(char) < 128 for char in key):
        raise ValueError("Key must only contain ASCII characters.")

    lowered_keys = {k.lower(): v for k, v in dictionary.items()}
    return lowered_keys.get(key.lower(), None)


_DEFAULT_CONF: typing.Final[dict] = {
    "logging": {
        "file": "<stderr>",
        "level": "info",
        "fmt": "[%(levelname)-8s] %(message)s",
    },
}


class TarpitSupervisor:
    def __init__(self, config: dict):
        self.orig_config = dict_deep_update(
            _DEFAULT_CONF, config, copy_dest=True, list_strategy="extend"
        )

        logging.debug(self.orig_config)
        level = get_log_level(self.orig_config["logging"]["level"])
        fmt = "[Supervisor] " + self.orig_config["logging"]["fmt"]

        TarpitWorker.setup_main_logger(
            level, fmt, get_log_handler(self.orig_config["logging"]["file"])
        )
        self.event_store = EventStore()
        self._worker_process: asyncio.subprocess.Process | None = None
        self._start_time: float = 0.0

    @staticmethod
    async def _get_process_stats(
        pid: int,
    ) -> dict[str, typing.Any] | None:
        """Get process stats using ps command (BSD/Linux universal)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ps",
                "-p",
                str(pid),
                "-o",
                "rss=,etime=",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)

            if proc.returncode != 0:
                return None

            line = stdout.decode("utf-8").strip()
            if not line:
                return None

            parts = line.split()
            if len(parts) < 2:
                return None

            # Parse memory (KB)
            memory_kb = int(parts[0])

            # Parse elapsed time (format: [[dd-]hh:]mm:ss or seconds)
            etime_str = parts[1]
            cpu_seconds = 0

            if "-" in etime_str:
                # Format: dd-hh:mm:ss
                days_part, time_part = etime_str.split("-")
                cpu_seconds += int(days_part) * 86400
                etime_str = time_part

            time_parts = etime_str.split(":")
            if len(time_parts) == 3:  # hh:mm:ss
                cpu_seconds += (
                    int(time_parts[0]) * 3600
                    + int(time_parts[1]) * 60
                    + int(time_parts[2])
                )
            elif len(time_parts) == 2:  # mm:ss
                cpu_seconds += int(time_parts[0]) * 60 + int(time_parts[1])
            else:  # ss
                cpu_seconds += int(time_parts[0])

            return {
                "memory_kb": memory_kb,
                "cpu_seconds": cpu_seconds,
            }
        except Exception:
            return None

    def generate_worker_conf_bytes(self) -> bytes:
        worker_conf: dict = {}
        worker_conf["tarpits"] = self.orig_config["tarpits"]
        worker_conf["logging"] = {}
        worker_conf["logging"]["level"] = self.orig_config["logging"]["level"]
        worker_conf["logging"]["fmt"] = (
            "[Worker    ] " + self.orig_config["logging"]["fmt"]
        )
        worker_conf["logging"]["file"] = "<stderr>"
        worker_conf[
            "worker"
        ] = {}  ## TODO: use worker section to fine grain worker behavior
        worker_conf["tracing"] = {}
        worker_conf["tracing"]["enabled"] = True
        worker_conf["tracing"]["file"] = "<stdout>"
        logging.debug("conf for worker: %s", worker_conf)
        conf_bytes = bytes(json.dumps(worker_conf), encoding="utf8") + b"\n"
        # print(conf_bytes)
        return conf_bytes

    async def handle_worker_stdout(self, event):
        logging.debug(event)
        self.event_store.append(event)

    async def run_worker(self):
        self._worker_process = await asyncio.create_subprocess_exec(
            sys.executable,
            __file__,
            "serve",
            "--config",
            "-",
            "--config-format",
            "jsonl",
            "--standalone",
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=None,
        )

        assert self._worker_process.stdin is not None
        self._worker_process.stdin.write(self.generate_worker_conf_bytes())
        await self._worker_process.stdin.drain()
        self._worker_process.stdin.close()

        assert self._worker_process.stdout is not None
        while True:
            line = await self._worker_process.stdout.readline()
            if not line:
                break
            line = str(line, encoding="utf8")
            event_dict = json.loads(line)
            ev = _decode_event_from_dict(event_dict)
            await self.handle_worker_stdout(event=ev)

    async def run_rpc_server(self):
        socket_path = (
            os.environ.get("TARPITD_SOCKET") or _get_default_socket_path()
        )

        server = JsonRpcUnixServer(socket_path, name="tarpitd_rpc")

        @server.register_method("ping")
        async def ping() -> dict[str, typing.Any]:
            return {
                "pong": True,
                "server": "tarpitd.py",
                "version": __version__,
            }

        @server.register_method("system_info")
        async def system_info() -> dict[str, typing.Any]:
            return {
                "server": "tarpitd.py",
                "version": __version__,
                "started_at": self._start_time,
                "platform": {
                    "os": os.name,
                    "system": platform.system(),
                    "release": platform.release(),
                    "machine": platform.machine(),
                    "python_version": platform.python_version(),
                    "python_implementation": platform.python_implementation(),
                },
            }

        @server.register_method("worker_stats")
        async def worker_stats() -> dict[str, typing.Any]:
            """Get worker process statistics."""
            if self._worker_process is None or self._worker_process.pid is None:
                return {
                    "status": "not_running",
                    "pid": None,
                    "memory_kb": None,
                    "cpu_seconds": None,
                }

            pid = self._worker_process.pid
            stats = await TarpitSupervisor._get_process_stats(pid)

            if stats is None:
                return {
                    "status": "unknown",
                    "pid": pid,
                    "memory_kb": None,
                    "cpu_seconds": None,
                }

            return {
                "status": "running",
                "pid": pid,
                "memory_kb": stats["memory_kb"],
                "cpu_seconds": stats["cpu_seconds"],
            }

        @server.register_method("event_buffer_info")
        async def event_buffer_info() -> dict[str, typing.Any]:
            return {
                "size": "unlimited",
                "usage": self.event_store.get_count(),
                "storage_bytes": self.event_store.get_size(),
                "max_size_bytes": self.event_store.get_max_size(),
                "backend": self.event_store.get_backend(),
            }

        @server.register_method("query_events")
        async def query_events(
            catalog: str = "events",
            start: int = 1,
            end: int = 100,
            peer_ip: str | None = None,
            tarpit_name: str | None = None,
            ev_type: str | None = None,
        ) -> list[dict[str, typing.Any]]:
            """Query events from the event store.

            Args:
                catalog: Catalog name (currently only 'events')
                start: Start index (1-indexed, negative for reverse)
                end: End index (1-indexed, negative for reverse)
                peer_ip: Filter by peer IP address
                tarpit_name: Filter by tarpit name
                ev_type: Filter by event type

            Returns:
                List of event dictionaries
            """
            return self.event_store.query(
                catalog=catalog,
                start=start,
                end=end,
                peer_ip=peer_ip,
                tarpit_name=tarpit_name,
                ev_type=ev_type,
            )

        async def shutdown():
            await server.stop()

        await server.start()
        logging.info("JSON-RPC starts on: %s", socket_path)

        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass

    def run(self):
        self._start_time = time.time()
        gc.collect()

        async def _main():
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.run_worker())
                tg.create_task(self.run_rpc_server())

        asyncio.run(_main())


class TarpitCtl:
    def __init__(
        self, socket_path: str = ""
    ):  # default is set in body via _get_default_socket_path()
        self.socket_path = socket_path or _get_default_socket_path()
        self.client = JsonRpcUnixClient(self.socket_path, name="tarpitd_ctl")

    def _format_uptime(self, started_at: float) -> str:
        current_time = time.time()
        uptime_seconds = current_time - started_at
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def ping(self) -> None:
        try:
            result = self.client.call("ping")
            if result and result.get("pong") is True:
                server_name = result.get("server", "unknown")
                version = result.get("version", "unknown")
                print(f"Server: {server_name}")
                print(f"Version: {version}")
                print("Status: Running")
            else:
                print("Error: Unexpected response from server")
                sys.exit(1)
        except OSError as e:
            print(f"Error: Unable to connect to supervisor: {e}")
            sys.exit(1)

    def status(self) -> None:
        try:
            result = self.client.call("system_info")
            buffer_result = self.client.call("event_buffer_info")
            worker_result = self.client.call("worker_stats")

            if not result:
                print("Error: Unable to get system info")
                sys.exit(1)

            version = result.get("version", "unknown")
            started_at = result.get("started_at", 0)
            uptime = self._format_uptime(started_at)

            buffer_usage = buffer_result.get("usage", 0) if buffer_result else 0
            storage_bytes = (
                buffer_result.get("storage_bytes", 0) if buffer_result else 0
            )
            max_size_bytes = (
                buffer_result.get("max_size_bytes", 0) if buffer_result else 0
            )
            backend = (
                buffer_result.get("backend", "unknown")
                if buffer_result
                else "unknown"
            )

            # Format current size
            if storage_bytes < 1024:
                cur_size_str = f"{storage_bytes}B"
            elif storage_bytes < 1024 * 1024:
                cur_size_str = f"{storage_bytes / 1024:.0f}KB"
            else:
                cur_size_str = f"{storage_bytes / (1024 * 1024):.1f}MB"

            # Format max size
            if max_size_bytes < 1024:
                max_size_str = f"{max_size_bytes}B"
            elif max_size_bytes < 1024 * 1024:
                max_size_str = f"{max_size_bytes / 1024:.0f}KB"
            else:
                max_size_str = f"{max_size_bytes / (1024 * 1024):.1f}MB"

            # Calculate estimated max entries
            estimated_max = "unknown"
            if buffer_usage > 0 and storage_bytes > 0:
                avg_size = storage_bytes / buffer_usage
                est_max = int(max_size_bytes / avg_size)
                estimated_max = f"{est_max} est"

            print("Server: tarpitd.py")
            print(f"Version: {version}")
            print(f"Uptime: {uptime}")
            print(
                f"Event Buffer [{backend}]: {cur_size_str}/{max_size_str} "
                f"({buffer_usage}/{estimated_max})"
            )

            # Display platform info
            platform_info = result.get("platform", {})
            if platform_info:
                system = platform_info.get("system", "unknown")
                release = platform_info.get("release", "unknown")
                machine = platform_info.get("machine", "unknown")
                py_version = platform_info.get("python_version", "unknown")
                py_impl = platform_info.get("python_implementation", "unknown")
                print(
                    f"Platform: {system} ({release} - {machine}), "
                    f"Python {py_version} ({py_impl})"
                )

            # Display worker stats
            if worker_result:
                worker_status = worker_result.get("status", "unknown")
                worker_pid = worker_result.get("pid")
                worker_memory = worker_result.get("memory_kb")
                worker_cpu = worker_result.get("cpu_seconds")

                if worker_status == "running" and worker_pid:
                    memory_str = (
                        f"{worker_memory}KB" if worker_memory else "N/A"
                    )
                    cpu_str = (
                        self._format_uptime(time.time() - worker_cpu)
                        if worker_cpu
                        else "N/A"
                    )
                    print(
                        f"Worker: pid={worker_pid}, mem={memory_str}, "
                        f"uptime={cpu_str}"
                    )
                elif worker_status == "not_running":
                    print("Worker: not running")
                else:
                    print(f"Worker: {worker_status}")

        except OSError as e:
            print(f"Error: Unable to connect to supervisor: {e}")
            sys.exit(1)

    def logs(
        self,
        catalog: str,
        start: int,
        end: int,
        peer_ip: str | None,
        tarpit_name: str | None,
        ev_type: str | None,
        format: str,
    ) -> None:
        """Query and display events from the event store.

        Args:
            catalog: Catalog name (currently only 'events')
            start: Start index (1-indexed, negative for reverse)
            end: End index (1-indexed, negative for reverse)
            peer_ip: Filter by peer IP address
            tarpit_name: Filter by tarpit name
            ev_type: Filter by event type
            format: Output format ('cli' or 'jsonl')
        """
        try:
            events = self.client.call(
                "query_events",
                {
                    "catalog": catalog,
                    "start": start,
                    "end": end,
                    "peer_ip": peer_ip,
                    "tarpit_name": tarpit_name,
                    "ev_type": ev_type,
                },
            )

            if events is None:
                print("Error: Unable to query events")
                sys.exit(1)

            if format == "jsonl":
                for event in events:
                    print(json.dumps(event, cls=BytesLiteralEncoder))
            else:
                # CLI format - human readable
                for event in events:
                    self._print_event_cli(event)

        except OSError as e:
            print(f"Error: Unable to connect to supervisor: {e}")
            sys.exit(1)

    def _print_event_cli(self, event: dict) -> None:
        """Print a single event in human-readable CLI format."""
        # Format timestamp: 2026-01-01 12:00:00.099
        timestamp = event.get("timestamp", 0)
        dt = time.localtime(timestamp)
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", dt)
        # Add milliseconds
        ms = int((timestamp % 1) * 1000)
        time_str = f"{time_str}.{ms:03d}"

        ev_type = event.get("ev_type", "unknown")
        tarpit = event.get("tarpit_name", "-")
        pattern = event.get("tarpit_pattern", "-")
        peer_ip = event.get("peer_ip", "-")
        peer_port = event.get("peer_port", "-")

        print(f"[{time_str}] {ev_type}")
        print(f"  Tarpit: {tarpit} ({pattern})")
        print(f"  Peer: {peer_ip}:{peer_port}")

        metadata = event.get("metadata")
        if metadata:
            print(f"  Metadata: {metadata}")
        print()


class TarpitWorker:
    def __init__(self, config: dict):
        self.server: list = []
        self.merged_config = dict_deep_update(
            _DEFAULT_CONF, config, copy_dest=True, list_strategy="extend"
        )

        level = get_log_level(self.merged_config["logging"]["level"])
        fmt = self.merged_config["logging"]["fmt"]
        self.setup_main_logger(level, fmt, logging.StreamHandler(sys.stderr))

        tarpit_classes: list[BaseTarpit] = get_all_subclasses(BaseTarpit)

        self.available_tarpits: dict[str, typing.Any] = {}

        # set this to dict[str,BaseTarpit] will make mypy complain
        for c in tarpit_classes:
            if c.PATTERN_NAME != BaseTarpit.PATTERN_NAME:
                self.available_tarpits.update({c.PATTERN_NAME: c})
                logging.debug("discovered tarpit pattern: %s", c.PATTERN_NAME)

        for c in tarpit_classes:
            for alias in c.PATTERN_NAME_ALIAS:
                self.available_tarpits.update({alias: c})
                logging.debug(
                    "discovered tarpit pattern alias: %s as %s",
                    alias,
                    c.PATTERN_NAME,
                )

    async def async_run_server(self):
        try:
            async with asyncio.TaskGroup() as tg:
                for i in self.server:
                    try:
                        s = await i
                        addr = s.sockets[0].getsockname()
                        logging.debug(f"asyncio serving on {addr}")
                        tg.create_task(s.serve_forever())
                    except OSError as e:
                        logging.error("failed to run server. err: `%s`", e)
                # TODO: config Tracer here
                clean_privilege()
                gc.collect()
        except asyncio.CancelledError:
            logging.warning(
                "`async_run_server` task cancelled. shutting down worker."
            )
        finally:
            logging.info("shutdown complete.")

    def start_all_server(self):
        with asyncio.Runner() as runner:
            runner.run(self.async_run_server())

    def prepare_all_server(self):
        for name, tarpit_config in self.merged_config["tarpits"].items():
            tarpit_config["pattern"] = tarpit_config["pattern"].casefold()
            logging.info(
                "tarpitd is setting up %s (%s)", tarpit_config["pattern"], name
            )

            logging.debug("config: %s", tarpit_config)

            real_tarpit_conf = {"name": name} | tarpit_config

            # Remove necessary item in config
            real_tarpit_conf.pop("bind")
            real_tarpit_conf.pop("pattern")

            if self.available_tarpits.get(tarpit_config["pattern"]):
                pit: BaseTarpit = self.available_tarpits[
                    tarpit_config["pattern"]
                ](**real_tarpit_conf)
            else:
                logging.error(
                    "pattern %s does not exist!", tarpit_config["pattern"]
                )
                exit()

            logging.info("server bind: {}".format(tarpit_config["bind"]))
            logging.warning(
                "tarpitd is serving %s (%s)", tarpit_config["pattern"], name
            )
            for i in tarpit_config["bind"]:
                self.server.append(
                    pit.create_server(host=i["host"], port=i["port"])
                )

    @staticmethod
    def setup_main_logger(level, fmt, handler):
        logger = logging.getLogger()
        logger.setLevel(level)

        formatter = logging.Formatter(
            fmt=fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        handler.setFormatter(formatter)

        # Properly clean existing handlers
        for h in logger.handlers:
            logger.removeHandler(h)
            if hasattr(h, "close"):
                h.close()
        logger.addHandler(handler)

    def run(self):
        self.prepare_all_server()
        self.start_all_server()


def display_manual_unix(name):
    import subprocess

    match name:
        case "tarpitd.py.1":
            subprocess.run("less", input=_MANUAL_TARPITD_PY_1.encode())
        case "tarpitd.conf.5":
            subprocess.run("less", input=_MANUAL_TARPITD_CONF_5.encode())
        case _:
            print("Manual page not found:", name)


def main_cli():
    logging.basicConfig(
        format="[%(levelname)-8s] %(message)s", level=logging.WARNING
    )

    import argparse

    epilog = (
        "This Source Code Form is subject to the terms of the Mozilla Public \n"
        "License, v. 2.0. If a copy of the MPL was not distributed with this \n"
        "file, You can obtain one at https://mozilla.org/MPL/2.0/"
        "\n\n"
        "> This program was made on the lands of \n"
        "  the Aminoac people of the Amacinoas Nation. \n"
        "  We pay our respects to their Elders, past and present. \n"
        "  Sovereignty was never ceded. "
        "\n\n"
    )

    top_parser = argparse.ArgumentParser(
        prog="tarpitd.py",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
        description="making a port into tarpit",
    )

    subparsers = top_parser.add_subparsers(
        help="subcommand", dest="subparser_name"
    )

    serve_parser = subparsers.add_parser(
        "serve",
        help="serve one or more tarpits",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
    )

    group = serve_parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-c",
        "--config",
        help="specify config file",
        metavar="FILE",
        type=argparse.FileType("rb"),
    )

    group.add_argument(
        "-p",
        "--pattern",
        help="serve specified tarpit pattern",
        metavar="PATTERN:HOST:PORT",
        action="extend",
        nargs="+",
    )

    serve_parser.add_argument(
        "-v",
        "--verbose",
        help="become more detailed at output",
        action="count",
    )

    serve_parser.add_argument(
        "-r",
        "--rate-limit",
        help="set data transfer rate limit [only applies to `--pattern` defined tarpits]",
        action="store",
        type=int,
        default=None,
    )

    serve_parser.add_argument(
        "-t",
        "--trace",
        help="set client trace level [only applies to `--pattern` defined tarpits]",
        choices=["none", "access", "request"],
        default="none",
    )

    serve_parser.add_argument(
        "-e",
        "--validate-client",
        help="check the client before sending data [only applies to `--pattern` defined tarpits]",
        const="check",
        nargs="?",
        choices=["check", "none"],
    )

    serve_parser.add_argument(
        "--standalone",
        help="serve tarpit without supervisor process",
        action="store_true",
    )

    serve_parser.add_argument(
        "--config-format",
        help="set the config format",
        const="toml",
        nargs="?",
        choices=["toml", "json", "jsonl"],
    )

    def serve(args):
        global _MANUAL_TARPITD_PY_1, _MANUAL_TARPITD_CONF_5
        conf: dict = {}
        if args.pattern:
            conf = generate_conf_from_cli(args)
        elif args.config:
            match args.config_format:
                case "toml":
                    import tomllib

                    conf = tomllib.load(args.config)
                case "json":
                    conf = json.load(args.config)
                case "jsonl":
                    # Just read the first line
                    conf = json.loads(args.config.readline())
        else:
            print("No pattern or config given!")
            serve_parser.parse_args(["--help"])
            exit()
        if args.standalone:
            del _MANUAL_TARPITD_PY_1, _MANUAL_TARPITD_CONF_5
            worker = TarpitWorker(conf)
            worker.run()
        else:
            supervisor = TarpitSupervisor(conf)
            supervisor.run()

    serve_parser.set_defaults(func=serve)

    manual_parser = subparsers.add_parser(
        "manual",
        help="display built-in manual page",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
    )

    manual_parser.add_argument(
        "page",
        help="show full manual of this program",
        nargs="?",
        default="tarpitd.py.1",
        action="store",
    )

    def manual(args):
        display_manual_unix(args.page)

    manual_parser.set_defaults(func=manual)

    ctl_parser = subparsers.add_parser(
        "ctl",
        help="control and get information from running supervisor",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
    )

    ctl_parser.add_argument(
        "-s",
        "--socket",
        help="Unix domain socket path (default: /tmp/tarpitd_u<UID>.sock)",
        metavar="PATH",
        default=os.environ.get("TARPITD_SOCKET", ""),
        action="store",
    )

    ctl_subparsers = ctl_parser.add_subparsers(
        help="ctl subcommand", dest="ctl_subparser_name"
    )

    ctl_ping_parser = ctl_subparsers.add_parser(
        "ping",
        help="ping the supervisor to check if it's running",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
    )

    def ctl_ping(args):
        controller = TarpitCtl(args.socket)
        controller.ping()

    ctl_ping_parser.set_defaults(func=ctl_ping)

    ctl_status_parser = ctl_subparsers.add_parser(
        "status",
        help="show supervisor status",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
    )

    def ctl_status(args):
        controller = TarpitCtl(args.socket)
        controller.status()

    ctl_status_parser.set_defaults(func=ctl_status)

    ctl_logs_parser = ctl_subparsers.add_parser(
        "logs",
        help="query and display event logs",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
    )

    ctl_logs_parser.add_argument(
        "-r",
        "--range",
        metavar="START,END",
        help="Range of events to display (1-indexed, negative for reverse). "
        "Example: --range=1,5 (first 5 events), --range=-1,-5 (last 5 events)",
        default="1,100",
    )

    ctl_logs_parser.add_argument(
        "-c",
        "--catalog",
        metavar="CATALOG",
        help="Catalog to query (currently only 'events')",
        default="events",
        choices=["events"],
    )

    ctl_logs_parser.add_argument(
        "-f",
        "--format",
        metavar="FORMAT",
        help="Output format: 'cli' (human-readable) or 'jsonl' (JSON lines)",
        default="cli",
        choices=["cli", "jsonl"],
    )

    ctl_logs_parser.add_argument(
        "--peer-ip",
        metavar="IP",
        help="Filter by peer IP address. Supports exact match (192.168.1.1), "
        "wildcard (192.168.1.*), or CIDR (192.168.1.0/24)",
        default=None,
    )

    ctl_logs_parser.add_argument(
        "--tarpit",
        metavar="NAME",
        help="Filter by tarpit name",
        default=None,
    )

    ctl_logs_parser.add_argument(
        "--type",
        metavar="TYPE",
        help="Filter by event type (e.g., 'conn_open', 'conn_close')",
        default=None,
    )

    def ctl_logs(args):
        controller = TarpitCtl(args.socket)

        # Parse range
        try:
            range_parts = args.range.split(",")
            if len(range_parts) != 2:
                raise ValueError("Range must be START,END")
            start = int(range_parts[0])
            end = int(range_parts[1])
        except (ValueError, IndexError) as e:
            print(f"Error: Invalid range format '{args.range}': {e}")
            print("Range must be in format: START,END (e.g., 1,100 or -1,-10)")
            sys.exit(1)

        controller.logs(
            catalog=args.catalog,
            start=start,
            end=end,
            peer_ip=args.peer_ip,
            tarpit_name=args.tarpit,
            ev_type=args.type,
            format=args.format,
        )

    ctl_logs_parser.set_defaults(func=ctl_logs)

    args = top_parser.parse_args()

    if not args.__contains__("func"):
        top_parser.parse_args(["--help"])
    else:
        args.func(args)


if __name__ == "__main__":
    main_cli()
