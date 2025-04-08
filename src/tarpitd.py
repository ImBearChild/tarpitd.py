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
        [-s SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]] [--manual]

## DESCRIPTION

Tarpitd.py will listen on specified ports and trouble clients that
connect to it. For more information on tarpitd.py, please refer to
[tarpitd.py(7)](./tarpitd.py.7.md), or use:

    tarpitd.py --manual tarpitd.py.7

## OPTIONS

#### `-c, --config [FILE]`

Load configuration from file.

#### `-s, --serve TARPIT:HOST:PORT [SERVICE:HOST:PORT ...]`

Start a tarpit on specified host and port. The name of tarpit is case-
insensitive. For the full list of supported tarpits, please refer to
[tarpitd.py(7)](./tarpitd.py.7.md)

#### `-r RATE, --rate-limit RATE`

Set data transfer rate limit. Positive value limit transfer speed to
RATE *byte* per second. Negative value will make program send one byte
in RATE second. (In other word, negative vale means 1/RATE byte per
second.)

## EXAMPLES

Print this manual:

    tarpitd.py --manual

Start an endlessh tarpit:

    tarpitd.py -s endlessh:0.0.0.0:2222

Start an endless HTTP tarpit on 0.0.0.0:8080, send a byte every two
seconds:

    tarpitd.py -r-2 -s HTTP_ENDLESS_COOKIE:0.0.0.0:8088

Start an endless HTTP tarpit on 0.0.0.0:8088, limit the transfer speed
to 1 KB/s:

    tarpitd.py -r1024 -s HTTP_DEFLATE_HTML_BOMB:0.0.0.0:8088

Start two different HTTP tarpit at the same time (the name of tarpit
is case-insensitive):

    tarpitd.py -s http_deflate_html_bomb:127.0.0.1:8080 \
                  HTTP_ENDLESS_COOKIE:0.0.0.0:8088

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]
"""
# =============================================================================

# =============================================================================
# Manual: tarpitd.py.7
# -----------------------------------------------------------------------------
_MANUAL_TARPITD_PY_7 = r""" 
## NAME

tarpitd.py - information about tarpit services in tarpitd.py

## GENERAL DESCRIPTION

Note: This section is for general information. And for description on
available tarpits, please refer to TARPITS section.

### TL;DR

Tarpitd.py will listen on specified ports and trouble clients that
connect to it.

### What is a "tarpit"

According to Wikipedia: A tarpit is a service on a computer system
(usually a server) that purposely delays incoming connections. The
concept is analogous with a tar pit, in which animals can get bogged
down and slowly sink under the surface, like in a swamp.

Tarpitd.py will partly simulate common internet services, for an
instance, HTTP, but respond in a way that may make the client not work
properly, slow them down or make them crash.

### Why I need a "tarpit"

This is actually a good thing in some situations. For example, an evil
ssh client may connect to port 22, and tries to log with weak
passwords. Or evil web crawlers can collect information from your
server, providing help for cracking your server.

You can use tarpit to slow them down.

### What is a service in tarpitd.py

A tarpit in tarpitd.py represent a pattern of response.

For an instance, to fight a malicious HTTP client, tarpitd.py can hold
on the connection by slowly sending an endless HTTP header, making it
trapped (`http_endless_header`). Also, tarpitd.py can send a malicious
HTML back to the malicious client, overloading its HTML parser
(`http_deflate_html_bomb`).

Different responses have different consequences, and different clients
may handle the same response differently. So even for one protocol,
there may be more than one "tarpit" in tarpitd.py correspond to it.

### Resource consumption

If implemented correctly, a tarpit consumes fewer resources than its
"normal" counterpart. Usually, a real server program will process
request from client and return response to it. But a tarpit don't need
to implement these parts.

For example, a real HTTP server will parse HTTP request and call CGI
(Python, PHP...) to generate a valid response. But tarpitd.py will
directly send a pre-generated content or several random bytes.

The reality is that when searching online for "how much memory does
Apache HTTPd require at least", most answers are hundreds of MB or
several GB. But tarpitd.py just need 2.5 MB of ram to serve an HTML
bomb, and 4/5 of memory is used by the bomb itself.

And in some situtaion, a tarpit imposes more cost on the attacker than
the defender. The HTML bomb is an good exmaple for this. If an
attacker chooses to parse it, he will spend more time than defender.
And if the attacker is only interested in HTTP header, the time the
defender spend on generating the bomb is wasted.

## TARPITS

### HTTP

#### http_endless_header

Tested with client: Firefox, Chromium, curl

Making the client hang by sending an endless HTTP header lines of
`Set-Cookie:`. Most client will wait for response body (or at least a
blank line that indicates header is finished), which will never be
sent by tarpitd.py.

#### http_deflate_html_bomb

Tested with client: Firefox, Chromium

A badly formed HTML compressed by deflate (zlib) will be sent by
tarpitd.py. It's so bad that most client will waste a lot of time
(more precisely, CPU time) on parsing it.

Some client won't bother to parse HTML, so this may not useful for
them. Content sent by this service is always compressed with deflate
algorithm, no matter if client support it or not. Because it's
pointless to serve uncompressed garbage, which may cause huge
potential waste of bandwidth, and most clients support deflate
algorithm.

#### http_deflate_size_bomb

Tested with client: Firefox, Chromium, curl

Feeding client with a lot of compressed zero. The current
implementation sends a compressed 1 MB file, which is approximately 1
GB decompressed, plus some invalid HTML code to trick client. And
deflate compress algorithm has its maximum compression rate limit, at
1030.3:1.

Curl won't decompress content by default. If you want to test this
with curl, please add `--compressed` option to it, and make sure you
have enough space for decompressed data.

### SSH

#### endlessh

Have been tested with client: openssh

Endlessh is a famous ssh tarpit. It keeps SSH clients locked up for
hours or even days at a time by sending endless banners. Despite its
name, technically this is not SSH, but an endless banner sender.
Endless does implement no part of the SSH protocol, and no port
scanner will think it is SSH (at least nmap and censys don't mark this
as SSH).

### ssh_trans_hold

Have been tested with client: openssh

This tarpit will keep the connection open by sending valid SSH
transport message. It follows IETF RFC 4253 (The Secure Shell (SSH)
Transport Layer Protocol).

First, it acts like a normal SSH server, sending identification
string, and send key exchange message about algorithm negotiation
after it. But it won't complete the key exchange, instead, sending
SSH_MSG_IGNORE repeatedly. The standard notes that clients MUST ignore
those message, but keeping receiving data will keep connection open.
So those clients will never disconnect.

The current implementation reports itself as OpenSSH 8.9 on Ubuntu and
replays a pre-recorded OpenSSH key exchange algorithm negotiation
request. This behavior may change in the future and affect the
reporting results of some port scanners.

### MISC

#### egsh_aminoas

Have been tested with client: openssh

This service can be used as an alternative to endlessh.

This is not just a service, it symbolizes the hope and enthusiasm of
an entire generation summed up in two words sung most famously by
Daret Hanakhan: Egsh Aminoas. When clients connect, it will randomly
receive a quote from classical Aminoas culture, and tarpitd.py will
show you the same quote in log at the same time.

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
import types
import enum
import zlib
import http

# module for cli use only will be import when needed


class TarpitWriter:
    """
    Wraps a asyncio.StreamWriter, adding speed limit on it.
    """

    async def write_and_drain(self, data):
        raise NotImplementedError

    async def _write_with_interval(self, data):
        for b in range(0, len(data)):
            await asyncio.sleep(abs(self.rate))
            self.writer.write(data[b : b + 1])
        await self.writer.drain()

    async def _write_normal(self, data):
        self.writer.write(data)
        await self.writer.drain()

    async def _write_with_speedlimit(self, data):
        """
        Send data in under a speed limit. Send no more than "rate" bytes per second.
        This function is used when crate TarpitWriter with positive "rate" value.
        """
        length = len(data)
        count = length // self.rate
        for b in range(0, count):
            await asyncio.sleep(1)
            self.writer.write(data[b * self.rate : (b + 1) * self.rate])
        self.writer.write(data[(count) * self.rate :])
        await self.writer.drain()

    def change_rate_limit(self, rate: int):
        logging.debug(f"rate limit: {rate}")
        self.rate = rate
        if rate == 0:
            self.write_and_drain = self._write_normal
        elif rate < 0:
            self.write_and_drain = self._write_with_interval
        else:
            self.write_and_drain = self._write_with_speedlimit

    def __init__(self, rate, writer: asyncio.StreamWriter) -> None:
        self.writer = writer
        self.drain = writer.drain
        self.close = writer.close
        self.wait_closed = writer.wait_closed
        self.change_rate_limit(rate)

    pass


class BaseTarpit:
    """
    This class should not be used directly.
    """

    @property
    def _DEFAULT_CONFIG():
        """
        Derived classes MAY overriding this in case they want to override default settings
        """
        return {"client_trace": True, "max_clients": 64, "rate_limit": -1}

    def _setup(self):
        """
        Setting up the Tarpit

        Classes that inherit this Class can implement this method
        as an alternative to overloading __init__.
        """
        return

    def log_client(self, event, source, destination, comment=None):
        self.logger.info(f"client_trace:[ {source} > {destination} ]:{event}:{comment}")

    async def _real_handler(self, reader, writer: TarpitWriter):
        """
        Callback for providing service

        Classes that inherit this Class SHOULD overload this method.
        """
        raise NotImplementedError

    def wrap_handler(self, local_address_port, real_handler: types.FunctionType):
        """
        This closure is used to pass listening address and port to
        handler running in asyncio
        """

        async def handler(reader, writer: asyncio.StreamWriter):
            async with self.sem:
                try:
                    try:
                        peername = writer.get_extra_info("peername")
                        self.log_client(
                            "open",
                            f"{peername[0]}:{peername[1]}",
                            f"{local_address_port}",
                        )
                        tarpit_writer = TarpitWriter(
                            self._config["rate_limit"], writer=writer
                        )
                        await real_handler(reader, tarpit_writer)
                    except (  # Log client
                        BrokenPipeError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                    ) as e:
                        self.log_client(
                            "close",
                            f"{peername[0]}:{peername[1]}",
                            f"{local_address_port}",
                            f"{e}",
                        )
                except Exception as e:
                    self.logger.exception(e)

        return handler

    async def create_server(self, host, port, start_serving=False):
        """
        Create a TCP server of this Tarpit and listen on the port of host address.

        Returns a asyncio.Server object.

        This function won't start the server immediately.
        The user should await on Server.start_serving() or
        Server.serve_forever() to make the server to start accepting connections.
        """
        return await asyncio.start_server(
            self.wrap_handler(f"{host}:{port}", self._real_handler), host, port
        )

    def __init__(self, **config) -> None:
        """
        Classes that inherit this Class SHOULD NOT overload this method.
        **options can be used to pass argument
        """
        self.logger = logging.getLogger(__name__)
        self._config = {}

        # Merge default config with method resolution order
        mro = self.__class__.__mro__
        for parent in reversed(mro):
            if parent is object:
                continue
            if t := getattr(parent, "_DEFAULT_CONFIG", None):
                self.logger.debug(
                    "merge default options from {}".format(parent.__name__)
                )
                self._config |= t.fget()

            # print("options: {}".format(options))

        # Remove None item from config
        for k, v in config.copy().items():
            if v is None:
                config.pop(k)

        self._config |= config
        self.logger.debug(self._config)
        self.sem = asyncio.Semaphore(self._config["max_clients"])
        if not self._config["client_trace"]:
            self.log_client = lambda a: None
        self._setup()


class EchoTarpit(BaseTarpit):
    async def _real_handler(self, reader, writer: TarpitWriter):
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
        writer.close()
        await writer.wait_closed()


class EndlessBannerTarpit(BaseTarpit):
    async def _real_handler(self, reader, writer: TarpitWriter):
        while True:
            await writer.write_and_drain(b"%x\r\n" % random.randint(0, 2**32))


class EgshAminoasTarpit(BaseTarpit):
    # cSpell:disable
    # These is a joke
    # https://github.com/HanaYabuki/aminoac
    AMINOCESE_DICT = {
        "Egsh Aminoas": "en:Song of Aminoas",
        "Aminoas": "en:Aminoas",
        "Ama Cinoas": "en:my beautiful homeland",
        "Yegm Laminoas": "en:no matter when, my heart yearns for you",
    }

    _aminocese_cache = []

    # cSpell:enable
    async def _real_handler(self, reader, writer: TarpitWriter):
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
class HttpConnection:
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
        self, code: int, phrase: bytes = None, version: bytes = b"HTTP/1.1"
    ):
        status = http.HTTPStatus(code)
        await self.writer.write_and_drain(
            b"%s %d %s\r\n" % (version, status, bytes(status.phrase, "ASCII"))
        )
        await self.send_raw(b"Server: Apache/2.4.9\r\nX-Powered-By: PHP/5.1.2-1+b1\r\n")
        pass

    async def send_header(self, keyword: bytes, value: bytes):
        await self.writer.write_and_drain(b"%s: %s\r\n" % (keyword, value))
        pass

    async def end_headers(self):
        await self.writer.write_and_drain(b"\r\n")

    async def send_content(
        self,
        content: bytes,
        type_: bytes = b"text/html; charset=UTF-8",
        encoding: bytes = None,
    ):
        await self.send_header(b"Content-Type", type_)
        await self.send_header(b"Content-Length", b"%d" % len(content))
        if encoding:
            await self.send_header(b"Content-Encoding", encoding)
        await self.end_headers()
        await self.send_raw(content)
        pass

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    def __init__(self, reader, writer: TarpitWriter) -> None:
        self.reader = reader
        self.writer = writer
        self.send_raw = writer.write_and_drain
        pass

    pass


class HttpTarpit(BaseTarpit):
    HTTP_STATUS_LINE_200 = (
        b"HTTP/1.1 200 OK\r\nServer: Apache/2.4.9\r\nX-Powered-By: PHP/5.1.2-1+b1\r\n"
    )

    async def _http_handler(self, connection: HttpConnection):
        pass

    async def _real_handler(self, reader, writer: TarpitWriter):
        conn = HttpConnection(reader, writer)
        await self._http_handler(conn)
        pass

    pass


class HttpOkTarpit(HttpTarpit):
    async def _http_handler(self, connection):
        await connection.send_status_line(200)
        await connection.close()


class HttpEndlessHeaderTarpit(HttpTarpit):
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


class HttpDeflateTarpit(HttpTarpit):
    @property
    def _DEFAULT_CONFIG():
        """
        Derived classes MAY overriding this in case they want to override default settings
        """
        return {
            "rate_limit": 16,
            "compression_type": "gzip",
        }

    async def _http_handler(self, connection: HttpConnection):
        await connection.send_status_line(200)
        await connection.send_content(
            self._deflate_content, encoding=bytes(self.compression_type, "ASCII")
        )
        return

    def _make_deflate(self, compressobj):
        raise NotImplementedError

    def _setup(self):
        self.compression_type = self._config["compression_type"]
        match self.compression_type:
            case "gzip":
                compressobj = zlib.compressobj(level=9, wbits=31)
            case "deflate":
                compressobj = zlib.compressobj(level=9, wbits=15)
        self._make_deflate(compressobj)

    pass


class HttpDeflateSizeBombTarpit(HttpDeflateTarpit):
    @property
    def _DEFAULT_CONFIG():
        """
        Derived classes MAY overriding this in case they want to override default settings
        """
        return {
            "rate_limit": 16,
            "compression_type": "deflate",
        }

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
    def _make_deflate(self, compressobj):
        self.logger.info("creating bomb...")
        # Don't use gzip, because gzip container contains uncompressed length
        # zlib stream have no uncompressed length, force client to decompress it
        # And they are SAME encodings, just difference in container format
        t = compressobj
        bomb = bytearray()
        # To successfully make Firefox and Chrome stuck, only zeroes is not enough
        bomb.extend(t.compress(b"<!DOCTYPE html><html><body>"))
        bomb.extend(t.compress(bytes(1024**2)))
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
        self.logger.info(f"deflate bomb created:{int(len(bomb) / 1024):d}kb")


#
# SSH
#


class SshMegNumber(enum.IntEnum):
    """
    RFC 4250 4.1

    The Message Number is a byte value that describes the payload of a
    packet.
    """

    SSH_MSG_IGNORE = 2
    SSH_MSG_UNIMPLEMENTED = 3
    SSH_MSG_DEBUG = 4


class SshTarpit(BaseTarpit):
    @classmethod
    def make_ssh_packet(cls, payload):
        packet = bytearray()
        total_length = 4 + 1 + len(payload)
        padding = 16 - (total_length % 8)
        packet += (total_length - 4 + padding).to_bytes(4)
        packet += padding.to_bytes(1)
        packet += payload
        packet += bytes(padding)
        return packet

    @classmethod
    def make_ssh_msg(cls, type: int, data):
        msg = bytearray(type.to_bytes())
        msg += data
        return msg

    @classmethod
    def make_ssh_msg_ignore(cls, length):
        return cls.make_ssh_msg(SshMegNumber.SSH_MSG_IGNORE, bytes(length))


class SshTransHoldTarpit(SshTarpit):
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

    async def _real_handler(self, reader, writer: TarpitWriter):
        later_rate = writer.rate
        if writer.rate < 128:
            # Change to a faster rate to send the KEX handshake
            writer.change_rate_limit(128)

        # Send identifier
        # RFC 4253:
        # Key exchange will begin immediately after sending this identifier.
        await writer.write_and_drain(
            # pretend to be ubuntu
            # see: https://svn.nmap.org/nmap/nmap-service-probes
            b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.3\r\n"
        )
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
            writer.change_rate_limit(later_rate)
            # SSH_MSG_IGNORE is allowed,
            # so keep sending this will keep connection open
            packet = self.make_ssh_packet(self.make_ssh_msg_ignore(16))
            await writer.write_and_drain(packet)

    pass


async def async_run_server(server):
    try:
        async with asyncio.TaskGroup() as tg:
            for i in server:
                s = await i
                addr = s.sockets[0].getsockname()
                logging.debug(f"asyncio serving on {addr}")
                tg.create_task(s.serve_forever())
    except asyncio.CancelledError:
        logging.info("`async_run_server` task cancelled. shutting down tarpitd.")
    finally:
        logging.info("shutdown complete.")


def run_server(server):
    with asyncio.Runner() as runner:
        runner.run(async_run_server(server))


def run_from_cli(args):
    config = {"tarpits": {}}
    number = 0
    for i in args.serve:
        p = i.casefold().partition(":")
        config["tarpits"][f"cli_{number}"] = {
            "type": p[0],
            "rate_limit": args.rate_limit,
            "bind": [{"host": p[2].partition(":")[0], "port": p[2].partition(":")[2]}],
        }
        number += 1
    run_from_config_dict(config)


def run_from_config_dict(config):
    server = []
    for k, v in config["tarpits"].items():
        pit = None
        v["type"] = v["type"].casefold()
        logging.info("tarpitd is serving {}({}) from config".format(v["type"], k))
        logging.debug(f"{v}")
        tarpit_conf = {"rate_limit": v.get("rate_limit")}
        match v["type"]:
            case "endlessh":
                pit = EndlessBannerTarpit(**tarpit_conf)
            case "http_endless_header":
                pit = HttpEndlessHeaderTarpit(**tarpit_conf)
            case "http_deflate_size_bomb":
                pit = HttpDeflateSizeBombTarpit(**tarpit_conf)
            case "http_deflate_html_bomb":
                pit = HttpDeflateHtmlBombTarpit(**tarpit_conf)
            case "egsh_aminoas":
                pit = EgshAminoasTarpit(**tarpit_conf)
            case "ssh_trans_hold":
                pit = SshTransHoldTarpit(**tarpit_conf)
            case other:
                print(f"service {other} is not exist!")
                exit()
        for i in v["bind"]:
            server.append(pit.create_server(host=i["host"], port=i["port"]))
    run_server(server)


def display_manual_unix(name):
    import subprocess

    match name:
        case "tarpitd.py.1":
            subprocess.run("less", input=_MANUAL_TARPITD_PY_1.encode())
        case "tarpitd.py.7":
            subprocess.run("less", input=_MANUAL_TARPITD_PY_7.encode())


def main_cli():
    logging.basicConfig(
        level=logging.DEBUG,
        # format=(
        #     #"%(name)s:%(levelname)s:%(message)s:"
        #     "{"
        #     '"message":"%(message)s",'
        #     '"created":%(created)f,"levelname":"%(levelname)s","funcName":"%(funcName)s",'
        #     '"module":"%(module)s","lineno":"%(lineno)d"'
        #     "}"
        # ),
    )
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
        nargs="?",
    )

    parser.add_argument(
        "-s",
        "--serve",
        help="serve specified tarpit",
        metavar="TARPIT:HOST:PORT",
        action="extend",
        nargs="+",
    )

    parser.add_argument(
        "--manual",
        help="show full manual of this program",
        nargs="?",
        const="tarpitd.py.1",
        action="store",
    )

    args = parser.parse_args()

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
