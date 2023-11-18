#!/usr/bin/env python3
# =============================================================================
# Manual: tarpitd.py.1
# -----------------------------------------------------------------------------
_MANUAL_TARPITD_PY_1=r"""
## NAME

tarpitd.py - a daemon making a port into tarpit

## SYNOPSIS

    tarpitd.py [-h] [-r RATE] 
        [-s SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]] [--manual]

## DESCRIPTION

Tarpitd.py will listen on specified ports and trouble clients that 
connect to it. For more information on tarpitd.py, please refer to 
[tarpitd.py(7)](./tarpitd.py.7.md), or use:

    tarpitd.py --manual tarpitd.py.7

## OPTIONS

`-s SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]`
`--serve SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]`

Start a service on specified host and port. 
The name of service is case-insensitive.

`-r RATE, --rate RATE`

Set data transfer rate limit.
Positive value limit transfer speed to RATE *byte* per second.
Negative value will make program send one byte in RATE second.
(In other word, negative vale means 1/RATE byte per second.)

## EXAMPLES

Print this manual:

    tarpitd.py --manual

Start an endlessh tarpit:

    tarpitd.py -s misc_endlessh:0.0.0.0:2222

Start an endless HTTP tarpit on 0.0.0.0:8080, send a byte every two
seconds:

    tarpitd.py -r-2 -s HTTP_ENDLESS_COOKIE:0.0.0.0:8088

Start an endless HTTP tarpit on 0.0.0.0:8088, limit the transfer speed
to 1 KB/s:

    tarpitd.py -r1024 -s HTTP_DEFLATE_HTML_BOMB:0.0.0.0:8088

Start two different HTTP tarpit at the same time
(the name of service is case-insensitive):

    tarpitd.py -s http_deflate_html_bomb:127.0.0.1:8080 \
                  HTTP_ENDLESS_COOKIE:0.0.0.0:8088 

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

"""
# =============================================================================

# =============================================================================
# Manual: tarpitd.py.7
# -----------------------------------------------------------------------------
_MANUAL_TARPITD_PY_7=r"""
## NAME

tarpitd.py - information about tarpit services in tarpitd.py

## GENERAL DESCRIPTION

Note: This section is for general information. And for description
on services, please refer to SERVICES section.

### TL;DR

Tarpitd.py will listen on specified ports and trouble clients that 
connect to it.

### What is a "tarpit"

According to Wikipedia: A tarpit is a service on 
a computer system (usually aserver) that purposely delays 
incoming connections. The concept is analogous with a tar pit, in
which animals can get bogged down and slowly sink under the surface,
like in a swamp. 

Tarpitd.py will partly simulate common internet services,
for an instance, HTTP, but respond in a way that may make the 
client not work properly, slow them down or make them crash.

### Why I need a "tarpit"

This is actually a good thing in some situations.
For example, an evil ssh client may connect to port 22,and tries to 
log with weak passwords. Or evil web crawlers can collect information
from your server, providing help for cracking your server.

You can use tarpit to slow them down.

### What is a service in tarpitd.py 

A service in tarpitd.py represent a pattern of response.

For an instance, to fight a malicious HTTP client, tarpitd.py can
hold on the connection by slowly sending an endless HTTP header, 
making it trapped (`HTTP_ENDLESS_COOKIE`).
Also, tarpitd.py can send a malicious HTML back
to the malicious client, overloading its HTML parser 
(`HTTP_DEFLATE_HTML_BOMB`). 

Different responses have different consequences, and different 
clients may handle the same response 
differently. So even for one protocol, there may be more than 
one `service` in tarpitd.py correspond to it.

## SERVICES

### HTTP_ENDLESS_COOKIE

Tested with client: Firefox, Chromium, curl

Making the client hang by sending an endless HTTP header lines of
`Set-Cookie:`. Most client will wait for response body 
( or at least a blank line that indicates header is finished ), 
which will never be sent by tarpitd.py.

### HTTP_DEFLATE_HTML_BOMB

Tested with client: Firefox, Chromium

A badly formed HTML compressed by deflate (zlib) will be sent by 
tarpitd.py. It's so bad that most client will waste a lot of time
(more precisely, CPU time ) on parsing it.

Some client won't bother to prase HTML, so this may not useful
for them.

### HTTP_DEFLATE_SIZE_BOMB

Tested with client: Firefox, Chromium, curl

Feeding client with a lot of compressed zero. The current 
implementation sends a compressed 1 MB file, which is approximately 
1 GB decompressed, plus some invalid HTML code to trick client.

Curl won't decompress content by default. If you want to test this 
with curl, please add `--compressed` option to it, and make sure you
have enough space for decompressed data.

### MISC_ENDLESSH

Have been tested with client: openssh

Endlessh is a famous ssh tarpit. It keeps SSH clients locked up for
hours or even days at a time by sending endless banners. Despite its 
name, technically this is not SSH, but an endless banner sender.
Endless does implement no part of the SSH protocol, and no port 
scanner will think it is SSH ( at least nmap and censys don't mark 
this as SSH).

The current implementation in tarpitd.py is just an alias of 
MISC_EGSH_AMINOAS.

### MISC_EGSH_AMINOAS

Have been tested with client: openssh

This service can be used as an alternative to endlessh.

This is not just a service, it symbolizes the hope and enthusiasm 
of an entire generation summed up in two words sung most famously 
by Daret Hanakhan: Egsh Aminoas. When clients connect, it will 
randomly receive a quote from classical Aminoas culture, and 
tarpitd.py will show you the same quote in log at the same time.

Hope this song will bring you homesickness. And remember ... 
You are always welcome in Aminoas.

"""
# =============================================================================


__version__ = "0.1.0"

import asyncio
import random
import logging


class TarpitWriter:
    def close(self):
        self.writer.close()

    async def write(self, data):
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
            await self.writer.drain()
        self.writer.write(data[(count) * self.rate :])
        await self.writer.drain()

    def __init__(self, rate, writer: asyncio.StreamWriter) -> None:
        self.rate = rate
        self.writer = writer
        self.drain = writer.drain
        if rate == 0:
            self.write = self._write_normal
        elif rate < 0:
            self.write = self._write_with_interval
        else:
            self.write = self._write_with_speedlimit

    pass


class Tarpit:
    protocol = "None"

    def get_handler(self, host, port):
        """This closure is used to pass listening address and port to
        handler running in asyncio"""

        async def handler(reader, writer: asyncio.StreamWriter):
            async with self.sem:
                try:
                    peername = writer.get_extra_info("peername")
                    self.logger.info(
                        f"CONN:OPEN:({peername[0]}:{peername[1]})=>({host}:{port})"
                    )
                    tarpit_writer = TarpitWriter(self.rate, writer=writer)
                    await self._handler(reader, tarpit_writer)
                except (
                    BrokenPipeError,
                    ConnectionAbortedError,
                    ConnectionResetError,
                ) as e:
                    self.logger.info(
                        f"CONN:CLOSE:({peername[0]}:{peername[1]})=>({host}:{port}):{e}"
                    )

        return handler

    async def start_server(self, host="0.0.0.0", port="8080"):
        """Start server
        Caller should set self._handler before call this method
        """
        return await asyncio.start_server(self.get_handler(host, port), host, port)

    def __init__(self, coro_limit=32, rate=None) -> None:
        self._handler = None
        self.rate = rate
        self.logger = logging.getLogger(self.protocol)
        self.sem = asyncio.Semaphore(coro_limit)


class MiscTarpit(Tarpit):
    protocol = "misc"

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

    async def _handler_egsh_aminoas(self, _reader, tarpit_writer: TarpitWriter):
        while True:
            a = random.choice(self._aminocese_cache)
            header = a.encode() + b"\r\n"
            await tarpit_writer.write(header)
            self.logger.info(a)

    # cSpell:enable

    async def start_server(self, host="0.0.0.0", port="8080"):
        return await asyncio.start_server(self.get_handler(host, port), host, port)

    def __init__(self, method="egsh_aminoas", coro_limit=32, rate=None) -> None:
        super().__init__()
        match method:
            case "egsh_aminoas":
                if not rate:
                    self.rate = -2
                # make a list first, so we don't generate it for every connection
                self._aminocese_cache = list(self.AMINOCESE_DICT.keys())
                self._handler = self._handler_egsh_aminoas
            case other:
                raise NotImplementedError
        if not self.rate:
            self.rate = rate


class HttpTarpit(Tarpit):
    protocol = "http"

    HTTP_START_LINE_200 = b"HTTP/1.1 200 OK\r\n"

    async def _handler_endless_cookie(self, _reader, tarpit_writer: TarpitWriter):
        await tarpit_writer.write(self.HTTP_START_LINE_200)
        while True:
            header = b"Set-Cookie: "
            await tarpit_writer.write(header)
            header = b"%x=%x\r\n" % (
                random.randint(0, 2**32),
                random.randint(0, 2**32),
            )
            await tarpit_writer.write(header)

    def _get_handler_deflate(self, data):
        async def fun(_reader, tarpit_writer: TarpitWriter):
            await tarpit_writer.write(self.HTTP_START_LINE_200)
            await tarpit_writer.write(
                b"Content-Type: text/html; charset=UTF-8\r\nContent-Encoding: deflate\r\n"
            )
            await tarpit_writer.write(b"Content-Length: %i\r\n\r\n" % len(data))
            await tarpit_writer.write(data)
            self.logger.info("MISC:deflate data sent")
            tarpit_writer.close()

        return fun

    def _generate_deflate_html_bomb(self):
        import zlib

        self.logger.info("MISC:creating bomb...")
        # Don't use gzip, because gzip container contains uncompressed length
        # zlib stream have no uncompressed length, force client to decompress it
        # And they are SAME encodings, just difference in container format
        t = zlib.compressobj(9)
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
        # The Maximum Compression Factor of zlib is about 1000:1
        # so 1024**2 means 1 MB original data, 1 KB after compression
        # According to https://www.zlib.net/zlib_tech.html
        # for _ in range(0, 1000):
        #     bomb.extend(t.compress(bytes(1024**2)))
        bomb.extend(t.compress(b"<table>MORE!</dd>" * 5))
        bomb.extend(t.flush())
        self.logger.info(f"MISC:html bomb created:{int(len(bomb)/1024):d}kb")
        self._deflate_html_bomb = bomb

    def _generate_deflate_size_bomb(self):
        self._generate_deflate_html_bomb()
        import zlib

        t = zlib.compressobj(9)
        bomb = self._deflate_html_bomb.copy()
        # The Maximum Compression Factor of zlib is about 1000:1
        # so 1024**2 means 1 MB original data, 1 KB after compression
        # According to https://www.zlib.net/zlib_tech.html
        for _ in range(0, 1000):
            bomb.extend(t.compress(bytes(1024**2)))
        bomb.extend(t.compress(b"<table>MORE!</dd>" * 5))
        bomb.extend(t.flush())
        self._deflate_size_bomb = bomb
        self.logger.info(f"MISC:deflate bomb created:{int(len(bomb)/1024):d}kb")

    def __init__(self, method="endless_cookie", coro_limit=32, rate=None) -> None:
        super().__init__()
        match method:
            case "endless_cookie":
                if not rate:
                    self.rate = -2
                self._handler = self._handler_endless_cookie
            case "deflate_size_bomb":
                if not rate:
                    self.rate = 1024
                self._generate_deflate_size_bomb()
                self._handler = self._get_handler_deflate(self._deflate_size_bomb)
            case "deflate_html_bomb":
                if not rate:
                    self.rate = 1024
                self._generate_deflate_html_bomb()
                self._handler = self._get_handler_deflate(self._deflate_html_bomb)
            case other:
                raise NotImplementedError
        if not self.rate:
            self.rate = rate
        self.logger.info(f"MISC:Server started:{self.rate}")
        # limit client amount


async def async_main(args):
    server = []
    for i in args.serve:
        p = i.casefold().partition(":")
        match p[0]:
            case "http_endless_cookie":
                pit = HttpTarpit("endless_cookie", rate=args.rate)
            case "http_deflate_html_bomb":
                pit = HttpTarpit("deflate_html_bomb", rate=args.rate)
            case "http_deflate_size_bomb":
                pit = HttpTarpit("deflate_size_bomb", rate=args.rate)
            case "misc_endlessh":
                pit = MiscTarpit("egsh_aminoas", rate=args.rate)
            case "misc_egsh_aminoas":
                pit = MiscTarpit("egsh_aminoas", rate=args.rate)
            case other:
                print(f"service {other} is not exist!")
                exit()

        bind = p[2].partition(":")
        server.append(pit.start_server(host=bind[0], port=bind[2]))
        logging.info(f"BIND:{p[0]}:{p[2]}:{args.rate}")
    await asyncio.gather(*server)
    while True:
        await asyncio.sleep(3600)


def display_manual_unix(name):
    import subprocess
    match name:
        case "tarpitd.py.1":
            subprocess.run("less", input=_MANUAL_TARPITD_PY_1.encode())
        case "tarpitd.py.7":
            subprocess.run("less", input=_MANUAL_TARPITD_PY_7.encode())


def main_cli():
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser(prog="tarpitd.py")

    # parser.add_argument(
    #     "-c", "--config", help="load configuration file", action="store"
    # )
    parser.add_argument(
        "-r",
        "--rate",
        help="set data transfer rate limit",
        action="store",
        type=int,
        default=None,
    )
    parser.add_argument(
        "-s",
        "--serve",
        help="run specified service",
        metavar="SERVICE:HOST:PORT",
        action="extend",
        nargs="+",
    )

    parser.add_argument(
        "--manual", help="show full manual of this program",nargs="?", const="tarpitd.py.1", action="store"
    )
    args = parser.parse_args()

    if args.manual:
        display_manual_unix(args.manual)
        pass
    elif args.serve:
        asyncio.run(async_main(args))
    else:
        parser.parse_args(["--help"])


if __name__ == "__main__":
    main_cli()
