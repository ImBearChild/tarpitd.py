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

    tarpitd.py [-h] [-r RATE] [-c [FILE]]
        [-s PATTERN:HOST:PORT [PATTERN:HOST:PORT ...]] [--manual]

## DESCRIPTION

tarpitd.py listens on specified network ports and purposefully delays or
troubles clients that connect to it. This tool can be used to tie up network
connections by delivering slow or malformed responses, potentially keeping
client connections open for extended periods.

## OPTIONS

#### `-c, --config FILE`

Load configuration from file.

#### `-s, --serve PATTERN:HOST:PORT [PATTERN:HOST:PORT ...]`

Start a tarpit pattern on the specified host and port.

The name of PATTERN is case-insensitive. For a complete list of supported
patterns, see the “TARPIT PATTERN” section below.

#### `-r RATE, --rate-limit RATE`

Set data transfer rate limit. Tarpits pattern has their own defalut value.

A positive value limits the transfer speed to RATE *bytes* per second. A
negative value causes the program to send one byte every |RATE| seconds
(effectively 1/|RATE| *bytes* per second).

#### `-t, --trace-client [FILE]`

Log client access to FILE. Disabled by default.

The output is in jsonl format. Logs to stdout if FILE is left blank.

#### `-e, --validate-client [{check, none}]`

Examine the client before sending a response. Enabled by default. Use `-e
none` to disable it.

The current implementation checks the first few bytes of the request to
confirm that the client is using the corresponding protocol.

#### `--manual MANUAL`

Display the built-in manual page. By default, tarpitd.py will open
`tarpitd.py.1`.

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

### SSH

#### endlessh

Tested with: OpenSSH

endlessh is a well-known SSH tarpit that traps SSH clients by sending endless
banner messages. Although named “endlessh”, it does not implement the full SSH
protocol; it simply emits continuous banner data. As a result, port scanners
(such as nmap and censys) will not mark the port as running a true SSH
service. tarpitd.py have this problem fixed by examining the client and
sending SSH identifier to scanners.

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

Print this manual:

    tarpitd.py --manual

Start an endlessh tarpit:

    tarpitd.py -s endlessh:0.0.0.0:2222

Start an endless HTTP tarpit with a 2-second per-byte delay:

    tarpitd.py -r-2 -s http_endless_header:0.0.0.0:8088

Start an endless HTTP tarpit with a rate limit of 1 KB/s:

    tarpitd.py -r1024 -s HTTP_DEFLATE_HTML_BOMB:0.0.0.0:8088

Start two different HTTP tarpit services concurrently (the name of the pattern
is case-insensitive):

    tarpitd.py -s http_deflate_html_bomb:127.0.0.1:8080 \
                  http_endless_header:0.0.0.0:8088

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

#### `client_trace=` (bool)

Enable logging of client access. Client validation result is logged with
access log.

## `[logging]` Table <!-- #### `main=` (str)

Path to the main log file. Sepcial value `<stdout>` and `<stderr>` is
supported.

Default is `<stderr>`. --> #### `client_trace=` (str)

Path to the client_trace log file. Sepcial value `<stdout>` and `<stderr>` is
supported.

Default is `<stdout>`.

## Example

```toml [tarpits] [tarpits.my_cool_ssh_tarpit] pattern = "ssh_trans_hold"
client_trace = true client_valiation = true max_clients = 8152 rate_limit = -2
bind = [{ host = "127.0.0.1", port = "2222" }]

[tarpits.http_tarpit] pattern = "http_endless_header" bind = [
  { host = "127.0.0.1", port = "8080" },
  { host = "::1", port = "8888" },
]

[tarpits.tls_tarpit] pattern = "tls_slow_hello" rate_limit = 1 bind = [
  { host = "127.0.0.1", port = "8443" },
]

[logging] client_trace = "./client_trace.log" ```

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

# module for cli use only will be import when needed


class BytesLiteralEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return repr(obj)
        return json.JSONEncoder.default(self, obj)


class TarpitWriter:
    """
    Wraps a asyncio.StreamWriter, adding speed limit on it.
    Do not have Writer.close(), since connection close should be handled outside
    """

    async def _write_with_interval(self, data):
        for b in range(0, len(data)):
            await asyncio.sleep(abs(self.rate))
            try:  # Handle Exception, because we are in loop
                self.writer.write(data[b : b + 1])
                await self.writer.drain()
            except (ConnectionResetError, BrokenPipeError) as e:
                raise e
                return
        await self.writer.drain()

    async def _write_normal(self, data):
        self.writer.write(data)
        await self.writer.drain()

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
                self.writer.write(data[b * self.rate : (b + 1) * self.rate])
                await self.writer.drain()
            except (ConnectionResetError, BrokenPipeError) as e:
                raise e
                return
        self.writer.write(data[(count) * self.rate :])
        await self.writer.drain()

    def change_rate_limit(self, rate: int):
        # logging.debug(f"rate limit: {rate}")
        self.rate = rate
        if rate == 0:
            write_inner = self._write_normal
        elif rate < 0:
            write_inner = self._write_with_interval
        else:
            write_inner = self._write_with_speedlimit

        self.write_and_drain: typing.Callable[[bytes], typing.Awaitable[None]] = (
            write_inner
        )

    def __init__(self, rate, writer: asyncio.StreamWriter) -> None:
        self.writer = writer
        self.drain = writer.drain
        # self.close = writer.close
        # self.wait_closed = writer.wait_closed
        # self.write_eof = writer.write_eof
        self.change_rate_limit(rate)


async def read_with_timeout(
    stream_reader: asyncio.StreamReader, n: int, timeout: float
) -> bytes:
    data = bytearray()
    try:
        async with asyncio.timeout(timeout):
            while len(data) < n:
                chunk = await stream_reader.read(n - len(data))
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

    class ValidatorConfig(typing.NamedTuple):
        head_allowlist: list[bytes] = []
        timeout: float = 2
        read_len: int = 4
        banner: bytes = b""
        response_failed: bytes = b""

    class ValidationResult(typing.NamedTuple):
        expected: bool
        data: bytes | None = None
        comment: str | None = None
        pass

    ValidatorCallable = typing.Callable[
        [asyncio.StreamReader, TarpitWriter],
        typing.Awaitable[ValidationResult],
    ]

    _validator_support: int = 0
    _validator_config: ValidatorConfig

    @dataclasses.dataclass
    class RuntimeConfig:
        name: str = "fixme:no_name"
        # name_pattern : str = "fixme:no_pattern_name"
        # TODO: make pattern name in class
        max_clients: int = 4096
        # Not real connection count. More than 4096 will be created, but will wait in queue
        # https://docs.python.org/3/library/socket.html#socket.socket.listen
        # default backlog is 100
        rate_limit: int = 1
        client_trace: bool = False
        client_validation: bool = True

        def update_from_dict(self, config_data: dict):
            for key, value in config_data.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)

    def _setup(self):
        """
        Setting up the Tarpit

        Classes that inherit this Class can implement this method
        as an alternative to overloading __init__.
        """

        if hasattr(super(), "_setup"):
            super()._setup()
            pass

        return

    async def _handle_client(self, reader: asyncio.StreamReader, writer: TarpitWriter):
        """
        Callback for providing service

        Classes that inherit this Class SHOULD overload this method.
        This method SHOULD NOT close connection when necessary.
        """
        raise NotImplementedError

    async def _validate_client(self, reader, writer):
        """
        Overload this if subclass want a different validator
        """
        conf = self._validator_config
        await writer.write_and_drain(conf.banner)
        data = await read_with_timeout(reader, conf.read_len, conf.timeout)
        for head in conf.head_allowlist:
            if data.startswith(head):
                return self.ValidationResult(True, data)
        await writer.write_and_drain(conf.response_failed)
        return self.ValidationResult(False, data)

    async def __fake_validate_client(self, reader, writer):
        return self.ValidationResult(True)  # Data is none means skipped

    # def _get_client_handler(
    #     self,
    # ) -> typing.Callable[
    #     [asyncio.StreamReader, asyncio.StreamWriter, ClientValidationResult],
    #     typing.Awaitable[None],
    # ]:
    #     raise NotImplementedError

    # def _get_client_validator(
    #     self,
    # ) -> typing.Callable[
    #     [asyncio.StreamReader, asyncio.StreamWriter],
    #     typing.Awaitable[ClientValidationResult],
    # ]:
    #     raise NotImplementedError

    def __log_client(
        self, writer: asyncio.StreamWriter, event: str, comment=None
    ) -> None:
        self.client_trace_logger.info(
            json.dumps(
                {
                    "time": time.time(),
                    "event": event,
                    "name": self._config.name,
                    "pattern": self.PATTERN_NAME,
                    "conn_info": {
                        "peername": writer.get_extra_info("peername"),
                        "sockname": writer.get_extra_info("sockname"),
                    },
                    "comment": comment,
                },
                cls=BytesLiteralEncoder,
            )
        )
        pass

    async def __handler(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        async with self.sem:
            try:
                self.__runtime_log_client(writer, "open")
                tarpit_writer = TarpitWriter(32, writer=writer)
                result = await self.__runtime_validate_client(reader, tarpit_writer)
                if result.expected:  # Only log for passed check
                    if result.data:
                        self.__runtime_log_client(
                            writer, "exam", comment=result._asdict()
                        )
                    tarpit_writer.change_rate_limit(self._config.rate_limit)
                    await self._handle_client(reader, tarpit_writer)
                    await writer.drain()

                    for i in range(4):  # 4 second timeout, 1 kb data
                        try:
                            if await asyncio.wait_for(reader.read(256), 1) == b"":
                                break
                        except asyncio.TimeoutError:
                            pass
                        pass

                    writer.close()
                    await writer.wait_closed()
                else:
                    self.__runtime_log_client(writer, "exam", comment=result._asdict())
                    writer.close()
                    await asyncio.sleep(random.randrange(16, 32))
                    await writer.wait_closed()
            except (  # Log client
                BrokenPipeError,
                ConnectionAbortedError,
                ConnectionResetError,
            ) as e:
                self.__runtime_log_client(writer, "conn_error", comment={"err": str(e)})
            except Exception as e:
                self.logger.exception(e)
            finally:
                self.__runtime_log_client(writer, "close")

    async def create_server(self, host, port, start_serving=False):
        """
        Create a TCP server of this Tarpit and listen on the port of host address.

        Returns a asyncio.Server object.

        This function won't start the server immediately.
        The user should await on Server.start_serving() or
        Server.serve_forever() to make the server to start accepting connections.
        """
        server = await asyncio.start_server(
            self.__handler,
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
        # Merge config
        self._config: BaseTarpit.RuntimeConfig = self.RuntimeConfig()
        # Use self.RuntimeConfig() here, so subclass can impl their own

        self._config.update_from_dict(config)
        self.logger.info(
            "server config: {}".format(self._config), dataclasses.asdict(self._config)
        )
        self.sem = asyncio.Semaphore(self._config.max_clients)

        # Merge validator config
        self._validator_config = self.ValidatorConfig()

        # Call setup for subclass setup
        self._setup()

        def _void(*args, **kwargs):
            pass

        async def _void_async(*args, **kwargs):
            pass

        # setup client_trace
        if self._config.client_trace:
            self.client_trace_logger = logging.getLogger(__name__ + ".client_trace")
            self.__runtime_log_client = self.__log_client
        else:
            self.__runtime_log_client = _void

        self.__runtime_validate_client: BaseTarpit.ValidatorCallable
        # setup client_validation
        if self._config.client_validation:
            match self._validator_support:
                case 1:
                    self.__runtime_validate_client = self._validate_client
                case _:
                    self.__runtime_validate_client = self.__fake_validate_client
                    self.logger.warning(
                        "this tarpit does not support client_validation"
                    )
        else:
            self.__runtime_validate_client = self.__fake_validate_client
            pass


# TODO Daymic
class EchoTarpit(BaseTarpit):
    PATTERN_NAME: str = "_internal_echo"

    async def _handle_client(self, reader, writer: TarpitWriter):
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


class EndlessBannerTarpit(BaseTarpit):
    PATTERN_NAME: str = "endless_banner"

    async def _handle_client(self, reader, writer: TarpitWriter):
        while True:
            await writer.write_and_drain(b"%x\r\n" % random.randint(0, 2**32))


class EgshAminoasTarpit(BaseTarpit):
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
    async def _handle_client(self, reader, writer: TarpitWriter):
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


class HttpTarpit(BaseTarpit):
    _validator_support = 1

    @dataclasses.dataclass
    class ValidatorConfig(BaseTarpit.ValidatorConfig):
        head_allowlist = [b"GET ", b"HEAD"]

    class Connection:
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

        async def send_status_line(self, code: int, version: bytes = b"HTTP/1.1"):
            status = http.HTTPStatus(code)
            await self.writer.write_and_drain(
                b"%s %d %s\r\n" % (version, status, bytes(status.phrase, "ASCII"))
            )
            await self.send_raw(
                b"Server: Apache/2.4.9\r\nX-Powered-By: PHP/5.1.2-1+b1\r\n"
            )
            pass

        async def send_header(self, keyword: bytes, value: bytes):
            await self.writer.write_and_drain(b"%s: %s\r\n" % (keyword, value))
            pass

        async def end_headers(self):
            await self.writer.write_and_drain(b"\r\n")

        async def send_content(
            self,
            content: bytes,
            type_: bytes = b"",
            encoding: bytes = b"",
        ):
            if len(type_):
                await self.send_header(b"Content-Type", type_)
            else:
                await self.send_header(b"Content-Type", b"text/html; charset=UTF-8")

            await self.send_header(b"Content-Length", b"%d" % len(content))
            if len(encoding):
                await self.send_header(b"Content-Encoding", encoding)
            await self.end_headers()
            await self.send_raw(content)
            pass

        async def close(self):
            """
            Do not use this without DynamicTarpit!
            """
            await self.writer.drain()
            self.writer.close()
            await self.writer.wait_closed()

        def __init__(self, reader, writer: TarpitWriter) -> None:
            self.reader = reader
            self.writer = writer
            self.send_raw = writer.write_and_drain
            pass

        pass

    async def _http_handler(self, connection: Connection):
        pass

    async def _handle_client(self, reader, writer: TarpitWriter):
        conn = HttpTarpit.Connection(reader, writer)
        await self._http_handler(conn)
        pass

    pass


class HttpOkTarpit(HttpTarpit):
    PATTERN_NAME: str = "_internal_http_ok"

    async def _http_handler(self, connection):
        await connection.send_status_line(200)
        await connection.send_content(b"DUCK!")
        # Left close to wrapped handler
        # await connection.close()


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
        pass

    class Content(typing.NamedTuple):
        data: bytes
        type_: str = ""
        encoding: str = ""
        pass

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

    pass


class HttpBadHtmlTarpit(HttpPreGeneratedTarpit):
    PATTERN_NAME = "http_bad_site"
    _BAD_SCRIPT = b"""
    for (;;) {
    console.log("DUCK");}
    """

    def _generate_content(self):
        data = bytearray()

        data.extend(
            b"<!DOCTYPE html><html><body><script src='/%x.js'></script><script>%s</script>"
            % (random.randint(0, 2**32), self._BAD_SCRIPT)
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

    pass


class HttpDeflateTarpit(HttpPreGeneratedTarpit):
    @dataclasses.dataclass
    class RuntimeConfig(HttpPreGeneratedTarpit.RuntimeConfig):
        rate_limit = 16
        compression_type = "gzip"
        pass

    def _make_deflate(self, compressobj):
        raise NotImplementedError

    def _generate_content(self):
        self._deflate_content = b""
        self.compression_type = (
            self._config.compression_type  # pytype: disable=attribute-error
        )
        match self.compression_type:
            case "gzip":
                compressobj = zlib.compressobj(level=9, wbits=31)
            case "deflate":
                compressobj = zlib.compressobj(level=9, wbits=15)
        self._make_deflate(compressobj)
        return self.Content(data=self._deflate_content, encoding=self.compression_type)

    pass


class HttpDeflateSizeBombTarpit(HttpDeflateTarpit):
    PATTERN_NAME: str = "http_deflate_size_bomb"

    @dataclasses.dataclass
    class RuntimeConfig(HttpTarpit.RuntimeConfig):
        rate_limit = 16
        compression_type = "deflate"
        pass

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


class SshTarpit(BaseTarpit):
    SSH_VERSION_STRING = b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.3\r\n"
    # pretend to be ubuntu
    # see: https://svn.nmap.org/nmap/nmap-service-probes

    _validator_support = 1

    @dataclasses.dataclass
    class ValidatorConfig(BaseTarpit.ValidatorConfig):
        head_allowlist = [b"SSH-"]
        response_failed = b""  # Cannot refer SSH_VERSION_STRING here

    ValidatorConfig.response_failed = SSH_VERSION_STRING

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

    async def _handle_client(self, reader, writer: TarpitWriter):
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

    pass


class SshEndlessTarpit(SshTarpit):
    PATTERN_NAME: str = "endlessh"

    async def _handle_client(self, reader, writer: TarpitWriter):
        while True:
            await writer.write_and_drain(b"%x\r\n" % random.randint(0, 2**32))


class TlsTarpit(BaseTarpit):
    PROTOCOL_VERSION_MAGIC = b"\x03\x03"  # TLS 1.2, also apply to 1.3

    _validator_support = 1

    @dataclasses.dataclass
    class ValidatorConfig(BaseTarpit.ValidatorConfig):
        head_allowlist = [b"\x16\x03"]


    # See: TLS 1.2 RFC ttps://www.rfc-editor.org/rfc/rfc5246#page-15
    class TlsRecordContentType(enum.IntEnum):
        HANDSHAKE = 22

    @classmethod
    def make_record(
        cls, content_type: TlsRecordContentType, fragment_data: bytes
    ) -> bytes:
        # TODO: make it
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
        frag = handshake_type.to_bytes(1, "big") + len(body).to_bytes(3, "big") + body
        return frag

    pass


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

    async def _handle_client(self, reader, writer: TarpitWriter):
        while True:
            packet = self.make_hello_request_record()
            await writer.write_and_drain(packet)

    pass


class TlsSlowHelloTarpit(TlsTarpit):
    PATTERN_NAME: str = "tls_slow_hello"

    @classmethod
    def make_server_hello_record(cls) -> bytes:
        padding_data_length = 2**14 - 1024
        session_ticket_data_length = 512
        session_id_length = 32  # Session ID 32 max

        renego_info_ext = b"\xff\x01\x00\x01\x00"  # 5 bytes
        ec_points_ext = (
            b"\x00\x0b\x00\x02\x01\x00"  # 6 bytes (type=0x0b, len=2, data=01 00)
        )
        ems_ext = b"\x00\x17\x00\x00"  # 4 bytes (type=0x17, len=0)

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
        cipher_suite = b"\xc0\x2f"  # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 (example)
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

    async def _handle_client(self, reader, writer: TarpitWriter):
        while True:
            await writer.write_and_drain(self._packet)

    def _setup(self):
        super()._setup()
        self._packet = self.make_server_hello_record()

    pass


class FtpTarpit(BaseTarpit):
    # https://www.rfc-editor.org/rfc/rfc959
    _validator_support = 1

    @dataclasses.dataclass
    class ValidatorConfig(BaseTarpit.ValidatorConfig):
        banner = (
            #b"220 (vsFTPd 3.0.5)\r\n"
            b"220 FileZilla Server 1.10.1\r\n"
            #b"220 Please visit https://filezilla-project.org/\r\n"
        )
        head_allowlist = [b"USER"]
        response_failed = b"530 Please login with USER.\r\n"

    pass


class FtpEndlessMotdTarpit(FtpTarpit):
    PATTERN_NAME: str = "ftp_endless_motd"

    async def _handle_client(self, reader, writer: TarpitWriter):
        await writer.write_and_drain(b"230-NOTICE: \r\n")
        while True:
            await writer.write_and_drain(b"230-%x\r\n" % random.randint(0, 2**32))


class SmtpTarpit(BaseTarpit):
    # https://datatracker.ietf.org/doc/html/rfc5321#appendix-D.1

    _validator_support = 1

    @dataclasses.dataclass
    class ValidatorConfig(BaseTarpit.ValidatorConfig):
        banner = (
            b"220 [127.0.0.1] ESMTP Sendmail 8.16.1/8.16.1; "
            b"Thu, 01 Jan 1970 00:00:00 +0000\r\n"
        )
        head_allowlist = [b"EHLO", b"HELO"]
        response_failed = b"502 Error: command not implemented.\r\n"

    pass


class SmtpEndlessEhloTarpit(SmtpTarpit):
    PATTERN_NAME: str = "smtp_endless_ehlo"

    async def _handle_client(self, reader, writer: TarpitWriter):
        await writer.write_and_drain(
            b"250-[127.0.0.1] Hello [192.168.1.1], pleased to meet you \r\n"
        )
        while True:
            await writer.write_and_drain(b"250-%x\r\n" % random.randint(0, 2**32))


async def async_run_server(server):
    try:
        async with asyncio.TaskGroup() as tg:
            for i in server:
                try:
                    s = await i
                    addr = s.sockets[0].getsockname()
                    logging.debug(f"asyncio serving on {addr}")
                    tg.create_task(s.serve_forever())
                except OSError as e:
                    logging.error("failed to run server. err: `%s`", e)
    except asyncio.CancelledError:
        logging.warning("`async_run_server` task cancelled. shutting down tarpitd.")
    finally:
        logging.info("shutdown complete.")


def run_server(server):
    with asyncio.Runner() as runner:
        runner.run(async_run_server(server))


def run_from_cli(args):
    config = {"tarpits": {}, "logging": {}}
    number = 0
    if args.trace_client and args.trace_client.name == "<stdout>":
        client_trace = True
        config["logging"]["client_trace"] = "<stdout>"
    elif args.trace_client:
        client_trace = True
        config["logging"]["file"] = args.trace_client.name
    else:
        client_trace = False
        logging.debug("no client trace config from cli")

    if args.validate_client == "check" or args.validate_client is None:
        client_validation = True
    else:
        client_validation = False

    if client_validation == "probe":
        raise NotImplementedError

    for i in args.serve:
        p = i.casefold().partition(":")
        config["tarpits"][f"cli_{number}"] = {
            "pattern": p[0],
            "rate_limit": args.rate_limit,
            "bind": [{"host": p[2].partition(":")[0], "port": p[2].partition(":")[2]}],
            "client_validation": client_validation,
            "client_trace": client_trace,
        }
        number += 1
    run_from_config_dict(config)


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def get_log_handler(file_name_in_conf):
    match file_name_in_conf:
        case "<stdout>":
            return logging.StreamHandler(sys.stdout)
        case "<stderr>":
            return logging.StreamHandler(sys.stderr)
        case _:
            return logging.FileHandler(file_name_in_conf)

    pass


def run_from_config_dict(config: dict):
    logging.warning("tarpid.py is running")
    server = []

    ct_enabled = False
    for name, tarpit_config in config["tarpits"].items():
        ct_enabled = ct_enabled or tarpit_config.get("client_trace")

    # Setup logger
    if ct_enabled:
        default_logging_conf = {"main": "<stderr>", "client_trace": "<stdout>"}
        if config.get("logging"):
            default_logging_conf.update(config["logging"])
        config["logging"] = default_logging_conf
        ct_logger = logging.getLogger(__name__ + ".client_trace")
        ct_logger.propagate = False
        if f_name := config["logging"]["client_trace"]:
            handler = get_log_handler(f_name)
        else:
            handler = get_log_handler("<stdout>")
            config["logging"]["client_trace"] = "<default_stdout>"
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        ct_logger.addHandler(handler)
        logging.info("saving client trace to `%s`", config["logging"]["client_trace"])
    else:
        logging.debug("no tarpit configured with client_trace, skip it")

    tarpit_classes: list[BaseTarpit] = get_all_subclasses(BaseTarpit)
    available_tarpits: dict[str, typing.Any] = {}
    # set this to dict[str,BaseTarpit] will make mypy complain
    for c in tarpit_classes:
        if c.PATTERN_NAME != BaseTarpit.PATTERN_NAME:
            available_tarpits.update({c.PATTERN_NAME: c})
            logging.debug("discovered tarpit pattern: %s", c.PATTERN_NAME)

    for name, tarpit_config in config["tarpits"].items():
        tarpit_config["pattern"] = tarpit_config["pattern"].casefold()
        logging.info("tarpitd is setting up %s (%s)", tarpit_config["pattern"], name)

        logging.debug("config: %s", tarpit_config)

        real_tarpit_conf = {"name": name} | tarpit_config
        real_tarpit_conf.pop("bind")  # Remove it since its useless

        if available_tarpits.get(tarpit_config["pattern"]):
            pit: BaseTarpit = available_tarpits[tarpit_config["pattern"]](
                **real_tarpit_conf
            )
        else:
            logging.error("pattern %s does not exist!", tarpit_config["pattern"])
            exit()

        logging.info("server bind: {}".format(tarpit_config["bind"]))
        logging.warning("tarpitd is serving %s (%s)", tarpit_config["pattern"], name)
        for i in tarpit_config["bind"]:
            server.append(pit.create_server(host=i["host"], port=i["port"]))

    run_server(server)


def display_manual_unix(name):
    import subprocess

    match name:
        case "tarpitd.py.1":
            subprocess.run("less", input=_MANUAL_TARPITD_PY_1.encode())
        case "tarpitd.conf.5":
            subprocess.run("less", input=_MANUAL_TARPITD_CONF_5.encode())


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(
        prog="tarpitd.py",
        formatter_class=argparse.RawTextHelpFormatter,
        description="making a port into tarpit",
        epilog=(
            "This Source Code Form is subject to the terms of the Mozilla Public \n"
            "License, v. 2.0. If a copy of the MPL was not distributed with this \n"
            "file, You can obtain one at https://mozilla.org/MPL/2.0/"
            "\n\n"
            "> This program was made on the lands of \n"
            "  the Aminoac people of the Amacinoas Nation. \n"
            "  We pay our respects to their Elders, past and present. \n"
            "  Sovereignty was never ceded. "
            "\n\n"
        ),
    )

    parser.add_argument(
        "-r",
        "--rate-limit",
        help="set data transfer rate limit",
        action="store",
        type=int,
        default=None,
    )

    parser.add_argument(
        "-c",
        "--config",
        help="specify config file",
        metavar="FILE",
        type=argparse.FileType("rb"),
    )

    parser.add_argument(
        "-t",
        "--trace-client",
        help="log client access to file",
        metavar="FILE",
        nargs="?",
        const="-",
        type=argparse.FileType("wb"),
    )

    parser.add_argument(
        "-e",
        "--validate-client",  # Verify?
        help="check the client before sending data",
        const="check",
        nargs="?",
        choices=["check", "none"],
        # TODO: make a probe option
        # check is short and simple, probe is longer
    )

    # TODO: IPv6 support of cli ( conf is supported )
    parser.add_argument(
        "-s",
        "--serve",
        help="serve specified tarpit pattern",
        metavar="PATTERN:HOST:PORT",
        action="extend",
        nargs="+",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="become more detailed at output",
        action="count",
    )

    parser.add_argument(
        "--manual",
        help="show full manual of this program",
        nargs="?",
        const="tarpitd.py.1",
        action="store",
    )

    args = parser.parse_args()

    logger = logging.getLogger()
    if not args.verbose:
        args.verbose = 0
        logger.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            fmt="[%(levelname)-8s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        logger.handlers = []
        logger.addHandler(handler)
    if args.verbose >= 1:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="[%(levelname)-8s - %(asctime)s] [%(name)s - %(funcName)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        logger.handlers = []
        logger.addHandler(handler)
    if args.verbose >= 2:
        logger.setLevel(logging.DEBUG)
    if args.verbose >= 3:
        logging.warning("higher verbose level is not implemented")

    if args.manual:
        display_manual_unix(args.manual)
        pass
    elif args.config:
        import tomllib

        if args.serve:
            print("--serve conflicts with --config")
            exit()
        run_from_config_dict(tomllib.load(args.config))
    elif args.serve:
        run_from_cli(args)
    else:
        parser.parse_args(["--help"])


if __name__ == "__main__":
    main_cli()
