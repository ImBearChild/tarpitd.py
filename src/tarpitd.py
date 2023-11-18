# =============================================================================
# Manual: tarpitd.py.1
# -----------------------------------------------------------------------------
_MANUAL_TARPITD_PY_1 = """
## NAME

tarpitd - a daemon making a port into tarpit

## SYNOPSIS

    tarpitd.py [-h] [-v] [-c CONFIG] [-r RATE] 
        [-s SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]] [--manual]

## DESCRIPTION

Tarpitd.py (tarpit daemon) is a python program that set up network
tarpits. A tarpit is a service on a computer system (usually a
server) that purposely delays incoming connections.

## EXAMPLES

Print this manual:

    tarpitd.py --manual

Start an endless HTTP tarpit on 0.0.0.0:8080, send a byte every two
seconds:

    tarpitd.py -r2 -s HTTP_ENDLESS_COOKIE:0.0.0.0:8088

Start two different HTTP tarpit at the same time:

    tarpitd.py -s http_deflate_size_bomb:0.0.0.0:8080 \\
                  HTTP_ENDLESS_COOKIE:0.0.0.0:8088 

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

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

    def __init__(self) -> None:
        self.rate = None
        self.logger = logging.getLogger(self.protocol)

class MiscTarpit(Tarpit):
    protocol = "misc"

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

    async def start_server(self, host="0.0.0.0", port="8080"):
        return await asyncio.start_server(self.get_handler(host, port), host, port)

    def __init__(self) -> None:
        super().__init__()


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
            await tarpit_writer.write(
                b"Content-Length: %i\r\n\r\n" % len(data)
            )
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
        self._handler = None
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
        if not self.rate:
            self.rate = rate
        self.sem = asyncio.Semaphore(coro_limit)
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

    subprocess.run("less", input=_MANUAL_TARPITD_PY_1.encode())


def main():
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser(prog="tarpitd")
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity\nss", action="store_true"
    )
    parser.add_argument(
        "-c", "--config", help="load configuration file", action="store"
    )
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
        "--manual", help="show full manual of this program", action="store_true"
    )
    args = parser.parse_args()

    if args.manual:
        display_manual_unix("")
        pass
    elif args.serve:
        asyncio.run(async_main(args))
    else:
        parser.parse_args(["--help"])


if __name__ == "__main__":
    main()
