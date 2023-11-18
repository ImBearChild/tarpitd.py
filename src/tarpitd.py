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
        return await asyncio.start_server(self.get_handler(host, port), host, port)

    def __init__(self) -> None:
        self.rate = 0
        self.logger = logging.getLogger(self.protocol)


class HttpTarpit(Tarpit):
    protocol = "HTTP"

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

    async def _handler_deflate_bomb(self, _reader, tarpit_writer: TarpitWriter):
        await tarpit_writer.write(self.HTTP_START_LINE_200)
        await tarpit_writer.write(
            b"Content-Type: text/html; charset=UTF-8\r\nContent-Encoding: deflate\r\n"
        )
        await tarpit_writer.write(
            b"Content-Length: %i\r\n\r\n" % len(self._deflate_bomb)
        )
        await tarpit_writer.write(self._deflate_bomb)
        self.logger.info("MISC:Bomb sent")
        tarpit_writer.close()
        pass

    def _generate_deflate_bomb(self):
        import zlib

        self.logger.info("MISC:Creating bomb...")
        # Don't use gzip, because gzip container contains uncompressed length
        # zlib stream have no uncompressed length, force client to decompress it
        # And they are SAME encodings, just difference in container format
        t = zlib.compressobj(9)
        bomb = bytearray()
        # The Maximum Compression Factor of zlib is about 1000:1
        # so 1024**3 means 1 MB after compression
        # According to https://www.zlib.net/zlib_tech.html
        bomb.extend(t.compress(bytes(1024**3)))
        bomb.extend(t.flush())
        self.logger.info(f"MISC:Bomb created:{int(len(bomb)/1024):d}kb")
        self._deflate_bomb = bomb

    def __init__(self, method="endless_cookie", coro_limit=2, rate=0) -> None:
        super().__init__()
        self._handler = None
        match method:
            case "endless_cookie":
                self._handler = self._handler_endless_cookie
            case "deflate_bomb":
                self._generate_deflate_bomb()
                self._handler = self._handler_deflate_bomb
        self.sem = asyncio.Semaphore(coro_limit)
        # limit client amount
        self.rate = rate


async def async_main(args):
    server = []
    for i in args.serve:
        p = i.casefold().partition(":")
        match p[0]:
            case "http_endless_cookie":
                pit = HttpTarpit("endless_cookie", rate=args.rate)
            case "http_deflate_bomb":
                pit = HttpTarpit("deflate_bomb", rate=args.rate)
        bind = p[2].partition(":")
        server.append(pit.start_server(host=bind[0], port=bind[2]))
        logging.info(f"BIND:{p[0]}:{p[2]}")
    await asyncio.gather(*server)
    while True:
        await asyncio.sleep(3600)

    exit()

    pit = HttpTarpit("deflate_bomb")
    s2 = await pit.start_server("0.0.0.0", 8081)
    async with s1, s2:
        while True:
            await asyncio.sleep(3600)


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
        "-r", "--rate", help="set data transfer rate limit", action="store", type=int
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
        print(__manual__)
        pass
    elif args.serve:
        asyncio.run(async_main(args))
    else:
        parser.parse_args(["--help"])


if __name__ == "__main__":
    main()
