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

#### `-s, --serve TARPIT:HOST:PORT [SERVICE:HOST:PORT ...]`  

Start a tarpit on specified host and port. 
The name of tarpit is case-insensitive. For the full list of 
supported tarpits, please refer to 
[tarpitd.py(7)](./tarpitd.py.7.md)

#### `-r RATE, --rate-limit RATE`

Set data transfer rate limit.
Positive value limit transfer speed to RATE *byte* per second.
Negative value will make program send one byte in RATE second.
(In other word, negative vale means 1/RATE byte per second.)

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

Start two different HTTP tarpit at the same time
(the name of tarpit is case-insensitive):

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
on available tarpits, please refer to TARPITS section.

### TL;DR

Tarpitd.py will listen on specified ports and trouble clients that 
connect to it.

### What is a "tarpit"

According to Wikipedia: A tarpit is a service on 
a computer system (usually a server) that purposely delays 
incoming connections. The concept is analogous with a tar pit, in
which animals can get bogged down and slowly sink under the surface,
like in a swamp. 

Tarpitd.py will partly simulate common internet services,
for an instance, HTTP, but respond in a way that may make the 
client not work properly, slow them down or make them crash.

### Why I need a "tarpit"

This is actually a good thing in some situations.
For example, an evil ssh client may connect to port 22, and tries to 
log with weak passwords. Or evil web crawlers can collect information
from your server, providing help for cracking your server.

You can use tarpit to slow them down.

### What is a service in tarpitd.py 

A tarpit in tarpitd.py represent a pattern of response.

For an instance, to fight a malicious HTTP client, tarpitd.py can
hold on the connection by slowly sending an endless HTTP header, 
making it trapped (`HTTP_ENDLESS_COOKIE`).
Also, tarpitd.py can send a malicious HTML back
to the malicious client, overloading its HTML parser 
(`HTTP_DEFLATE_HTML_BOMB`). 

Different responses have different consequences, and different 
clients may handle the same response differently. So even for one 
protocol, there may be more than one "tarpit" in tarpitd.py 
correspond to it.

### Resource consumption

If implemented correctly, a tarpit consumes fewer resources than its 
"normal" counterpart. Usually, a real server program will process 
request from client and return response to it. But a tarpit don't 
need to implement these parts.

For example, a real HTTP server will parse HTTP request and call CGI 
(Python, PHP...) to generate a valid response. But tarpitd.py will 
directly send a pre-generated content or several random bytes.

The reality is that when searching online for "how much memory does 
Apache HTTPd require at least", most answers are hundreds of MB or 
several GB. But tarpitd.py just need 2.5 MB of ram to serve an HTML 
bomb, and 4/5 of memory is used by the bomb itself. 

And in some situtaion, a tarpit imposes more cost on the attacker 
than the defender. The HTML bomb is an good exmaple for this. If an 
attacker chooses to parse it, he will spend more time than defender.
And if the attacker is only interested in HTTP header, the time the 
defender spend on generating the bomb is wasted. 

## TARPITS

### HTTP

#### http_endless_header

Tested with client: Firefox, Chromium, curl

Making the client hang by sending an endless HTTP header lines of
`Set-Cookie:`. Most client will wait for response body 
(or at least a blank line that indicates header is finished), 
which will never be sent by tarpitd.py. 

#### http_deflate_html_bomb

Tested with client: Firefox, Chromium

A badly formed HTML compressed by deflate (zlib) will be sent by 
tarpitd.py. It's so bad that most client will waste a lot of time
(more precisely, CPU time) on parsing it.

Some client won't bother to parse HTML, so this may not useful
for them. Content sent by this service is always compressed with
deflate algorithm, no matter client support it or not.
Because it's pointless to serve uncompressed garbage, which
may cause huge potential waste of bandwidth, and most
clients support deflate algorithm.

#### http_deflate_size_bomb

Tested with client: Firefox, Chromium, curl

Feeding client with a lot of compressed zero. The current 
implementation sends a compressed 1 MB file, which is approximately 
1 GB decompressed, plus some invalid HTML code to trick client.
And deflate compress algorithm has its maximum compression 
rate limit, at 1030.3:1.

Curl won't decompress content by default. If you want to test this 
with curl, please add `--compressed` option to it, and make sure you
have enough space for decompressed data.

### MISC

#### endlessh

Have been tested with client: openssh

Endlessh is a famous ssh tarpit. It keeps SSH clients locked up for
hours or even days at a time by sending endless banners. Despite its 
name, technically this is not SSH, but an endless banner sender.
Endless does implement no part of the SSH protocol, and no port 
scanner will think it is SSH (at least nmap and censys don't mark 
this as SSH).

The current implementation in tarpitd.py is just an alias of 
MISC_EGSH_AMINOAS.

#### egsh_aminoas

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
import types


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

    def __init__(self, rate, writer: asyncio.StreamWriter) -> None:
        self.rate = rate
        self.writer = writer
        self.drain = writer.drain
        self.close = writer.close
        self.wait_closed = writer.wait_closed
        if rate == 0:
            self.write_and_drain = self._write_normal
        elif rate < 0:
            self.write_and_drain = self._write_with_interval
        else:
            self.write_and_drain = self._write_with_speedlimit

    pass


class BaseTarpit:
    """
    This class should not be used directly.
    """
    def _setup(self):
        """
        Setting up the Tarpit

        Classes that inherit this Class can implement this method 
        as an alternative to overloading __init__. 
        """
        return

    def log_client(self, event, source, destination , comment=None):
        self.logger.info(f"client_trace:{event}:[ {source} > {destination} ]:{comment}")

    async def _real_handler(self, reader, writer: TarpitWriter):
        """
        Callback for providing service

        Classes that inherit this Class SHOULD overload this method.
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

    def wrap_handler(self, source_hint, real_handler: types.FunctionType):
        """
        This closure is used to pass listening address and port to
        handler running in asyncio
        """

        async def handler(reader, writer: asyncio.StreamWriter):
            async with self.sem:
                try:
                    peername = writer.get_extra_info("peername")
                    self.log_client(
                        "open", f"{peername[0]}:{peername[1]}", f"{source_hint}"
                    )
                    tarpit_writer = TarpitWriter(self.rate_limit, writer=writer)
                    await real_handler(reader, tarpit_writer)
                except (
                    BrokenPipeError,
                    ConnectionAbortedError,
                    ConnectionResetError,
                ) as e:
                    self.log_client(
                        "close", f"{peername[0]}:{peername[1]}", f"{source_hint}",f"{e}"
                    )

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

    def __init__(self, client_log=True, max_clients=32, rate_limit=16, **extra_options) -> None:
        """
        Classes that inherit this Class SHOULD NOT overload this method.
        **extra_options can be used to transfer extra argument
        """
        self.logger = logging.getLogger(__name__)
        self.sem = asyncio.Semaphore(max_clients)
        self.rate_limit = rate_limit
        self.extra_options = extra_options
        self._setup()
        if not client_log:
            self.log_client = lambda *a: None
        pass


class EndlessBannerTarpit(BaseTarpit):
    async def _real_handler(self, reader, writer: TarpitWriter):
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

class HttpTarpit(BaseTarpit):
    HTTP_STATUS_LINE_200 = b"HTTP/1.1 200 OK\r\n"
    pass

class HttpEndlessHeaderTarpit(HttpTarpit):
    async def _real_handler(self, reader, writer: TarpitWriter):
        await writer.write_and_drain(self.HTTP_STATUS_LINE_200)
        while True:
            header = b"Set-Cookie: "
            await writer.write_and_drain(header)
            header = b"%x=%x\r\n" % (
                random.randint(0, 2**32),
                random.randint(0, 2**32),
            )
            await writer.write_and_drain(header)

class HttpDeflateTarpit(HttpTarpit):
    async def _real_handler(self, reader, writer: TarpitWriter):
        await writer.write_and_drain(self.HTTP_STATUS_LINE_200)
        await writer.write_and_drain(
                b"Content-Type: text/html; charset=UTF-8\r\n"
                b"Content-Encoding: deflate\r\n"
            )
        await writer.write_and_drain(b"Content-Length: %i\r\n\r\n" % len(self._deflate_content))
        await writer.write_and_drain(self._deflate_content)
        self.logger.info("deflate data sent")
        writer.close()

    def _make_deflate(self):
        self._deflate_content = bytearray()
        pass
    
    def _setup(self):
        self._make_deflate()
    pass

class HttpDeflateSizeBombTarpit(HttpDeflateTarpit):
    def _make_deflate(self):
        import zlib

        t = zlib.compressobj(9)
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
        self.logger.info(f"deflate bomb created:{int(len(bomb)/1024):d}kb")

class HttpDeflateHtmlBombTarpit(HttpDeflateTarpit):
    def _make_deflate(self):
        import zlib

        self.logger.info("creating bomb...")
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
        bomb.extend(t.compress(b"<table>MORE!</dd>" * 5))
        bomb.extend(t.flush())
        self._deflate_content = bomb
        self.logger.info(f"deflate bomb created:{int(len(bomb)/1024):d}kb")


async def async_run_server(server):
    async with asyncio.TaskGroup() as tg:
        for i in server:
            s = await i
            addr = s.sockets[0].getsockname()
            logging.debug(f"asyncio serving on {addr}")
            tg.create_task(s.serve_forever())

def run_server(server):
    with asyncio.Runner() as runner:
        runner.run(async_run_server(server))


def run_from_cli(args):
    server = []
    for i in args.serve:
        p = i.casefold().partition(":")
        match p[0]:
            case "endlessh":
                pit = EndlessBannerTarpit(rate_limit=args.rate_limit)
            case "http_endless_header":
                pit = HttpEndlessHeaderTarpit(rate_limit=args.rate_limit)
            case "http_deflate_size_bomb":
                pit = HttpDeflateSizeBombTarpit(rate_limit=args.rate_limit)
            case "http_deflate_html_bomb":
                pit = HttpDeflateHtmlBombTarpit(rate_limit=args.rate_limit)
            case "egsh_aminoas":
                pit = EgshAminoasTarpit(rate_limit=args.rate_limit)
            case other:
                print(f"service {other} is not exist!")
                exit()
        bind = p[2].partition(":")
        server.append(pit.create_server(host=bind[0], port=bind[2]))
        logging.info(f"tarpitd is serving {p[0]} on {p[2]} with speed limit {args.rate_limit}")
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

    parser = argparse.ArgumentParser(prog="tarpitd.py")

    # parser.add_argument(
    #     "-c", "--config", help="load configuration file", action="store"
    # )
    parser.add_argument(
        "-r",
        "--rate-limit",
        help="set data transfer rate limit",
        action="store",
        type=int,
        default=None,
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
    elif args.serve:
        run_from_cli(args)
    else:
        parser.parse_args(["--help"])


if __name__ == "__main__":
    main_cli()
