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

- `-s, --socket PATH` - Specify the Unix domain socket path (default: /tmp/tarpitd.sock)
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