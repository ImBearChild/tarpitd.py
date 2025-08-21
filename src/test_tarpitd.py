import unittest
import asyncio
import tarpitd
import time
import typing


class TestTarpit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        pass

    def create_tarpit_obj(self):
        pass

    async def asyncSetUp(self):
        print("[TEST] set up test")
        pit = self.create_tarpit_obj()
        self.port = 0
        self.server = await pit.create_server("127.0.0.2", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.server.start_serving())
        print("[TEST] set up done")

    def tearDown(self):
        pass

    async def asyncTearDown(self):
        print("[TEST] teardown test")
        self.server.close()
        await self.server.wait_closed()
        print("[TEST] teardown test done")

    async def on_cleanup(self):
        pass


class TestRateLimitPositive(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.EndlessBannerTarpit(rate_limit=2)
        return t

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        t1 = time.time()
        await reader.readexactly(10)  # should take 5s
        t2 = time.time()

        self.assertTrue(abs((t2 - t1 - 5) / 5) < 0.5)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        self.addAsyncCleanup(self.on_cleanup)


class TestRateLimitNegative(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.EndlessBannerTarpit(rate_limit=-2)
        return t

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        t1 = time.time()
        await reader.readexactly(2)  # 4s
        t2 = time.time()

        self.assertTrue(abs((t2 - t1 - 4) / 4) < 0.5)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        self.addAsyncCleanup(self.on_cleanup)


class TestHttpTarpit(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.HttpEndlessHeaderTarpit(rate_limit=0)
        return t

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        writer.write(b"GET ")
        line = await reader.readline()
        self.assertTrue(line.startswith(b"HTTP"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        while True:
            line = await reader.readline()
            if line.startswith(b"Set-Cookie:"):
                self.assertFalse(line.find(b"=") == -1)
                break
        self.addAsyncCleanup(self.on_cleanup)



class TestTlsTarpit(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.TlsHelloRequestTarpit(rate_limit=0)
        return t

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        writer.write(b"\x16\x03\x03")
        line = await reader.read(8)
        self.assertTrue(line.startswith(b"\x16\x03\x03"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        self.addAsyncCleanup(self.on_cleanup)


class TestTlsSlowHelloTarpit(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.TlsSlowHelloTarpit(rate_limit=0)
        return t

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        writer.write(b"\x16\x03\x03")
        line = await reader.read(8)
        self.assertTrue(line.startswith(b"\x16\x03\x03\x3e\x63"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        self.addAsyncCleanup(self.on_cleanup)



# NEO


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


async def readline_with_timeout(
    stream_reader: asyncio.StreamReader, timeout: float
) -> bytes:
    data: bytes
    try:
        async with asyncio.timeout(timeout):
            data = await stream_reader.readline()
    except asyncio.TimeoutError:
        return b""
    return data


class TarpitTestSet(typing.NamedTuple):
    request: bytes | None
    excepted_response: (
        bytes
        | typing.Callable[
            [asyncio.StreamReader, asyncio.StreamWriter], typing.Awaitable[None]
        ]
    )
    config: dict = {"rate_limit": 1024}


class PreparedTarpitServer(typing.NamedTuple):
    port: int
    server: asyncio.Server
    test_set: TarpitTestSet


class NeoTestTarpit(unittest.IsolatedAsyncioTestCase):
    TARPIT = tarpitd.BaseTarpit
    TEST_SET: list[TarpitTestSet] = []

    def _setup(self):
        pass

    async def setup_tarpit(self, **conf):
        t = self.TARPIT(**conf)
        t_server = await t.create_server("127.0.0.2", 0)
        t_port = t_server.sockets[0].getsockname()[1]
        return (t_port, t_server)

    async def asyncSetUp(self) -> None:
        print("[TEST] set up test")
        self._setup()
        self.tarpits: list[PreparedTarpitServer] = []
        for i in self.TEST_SET:
            p, s = await self.setup_tarpit(**(i.config))
            self.tarpits.append(PreparedTarpitServer(p, s, i))

        async with asyncio.TaskGroup() as tg:
            for j in self.tarpits:
                tg.create_task(j.server.start_serving())
        print("[TEST] set up done")

    async def asyncTearDown(self):
        print("[TEST] teardown test")
        for i in self.tarpits:
            i.server.close()
            await i.server.wait_closed()
        print("[TEST] teardown test done")

    async def do_test_set(self, server: PreparedTarpitServer):
        port = server.port
        reader, writer = await asyncio.open_connection("127.0.0.2", port)

        request = server.test_set.request
        await asyncio.sleep(0)
        if isinstance(request, bytes):
            writer.write(request)
            await writer.drain()

        await asyncio.sleep(0)
        excepted_response = server.test_set.excepted_response
        if isinstance(excepted_response, bytes):
            data = await read_with_timeout(reader, len(excepted_response), 10)
            await asyncio.sleep(1)
            self.assertIn(excepted_response,data)
        else:
            await asyncio.sleep(1)
            await excepted_response(reader, writer)
        pass

    async def test_all(self):
        if self.__class__ is not NeoTestTarpit:
            for i in self.tarpits:
                print("running %s, %s, %s" % (i.port, i.server, i.test_set._asdict()))
                await self.do_test_set(i)


async def get_http_header(reader: asyncio.StreamReader) -> str:
    """
    Checks if the specified string is present in the headers read from the asyncio.StreamReader.
    """
    headers = b""
    for i in range(32):
        line = await readline_with_timeout(reader, 1)
        if line == b"\r\n":  # End of headers marker
            break
        headers += line

    decoded_headers = headers.decode("utf-8")
    return decoded_headers


class T_HttpOk(NeoTestTarpit):
    TARPIT = tarpitd.HttpOkTarpit
    TEST_SET: list[TarpitTestSet] = [
        TarpitTestSet(request=b"GET ", excepted_response=b"HTTP"),
        TarpitTestSet(request=b"BAD_", excepted_response=b""),
    ]


class T_HttpDeflateHtml(NeoTestTarpit):
    TARPIT = tarpitd.HttpDeflateHtmlBombTarpit

    async def have_gzip(self, reader, writer):
        header = await get_http_header(reader)
        self.assertFalse("deflate" in header)
        self.assertTrue("gzip" in header)

    TEST_SET: list[TarpitTestSet] = [
        TarpitTestSet(request=b"GET ", excepted_response=b"HTTP"),
        TarpitTestSet(request=b"BAD_", excepted_response=b""),
    ]

    def _setup(self):
        self.TEST_SET.append(
            TarpitTestSet(request=b"GET ", excepted_response=self.have_gzip)
        )


class T_HttpDeflateSize(NeoTestTarpit):
    TARPIT = tarpitd.HttpDeflateSizeBombTarpit

    async def have_deflate(self, reader, writer):
        header = await get_http_header(reader)
        self.assertTrue("deflate" in header)
        self.assertFalse("gzip" in header)

    TEST_SET: list[TarpitTestSet] = []

    def _setup(self):
        self.TEST_SET.append(
            TarpitTestSet(request=b"GET ", excepted_response=self.have_deflate)
        )


class T_SshValidatorExtra(NeoTestTarpit):
    class T(tarpitd.SshTransHoldTarpit):
        class ValidatorConfig(tarpitd.SshTransHoldTarpit.ValidatorConfig):
            response_failed = b"BAD_RESPONSE"

    TARPIT = T

    TEST_SET: list[TarpitTestSet] = [
        TarpitTestSet(request=b"SSH-FAKE", excepted_response=b"SSH-"),
        TarpitTestSet(request=b"BAD_", excepted_response=b"BAD"),
    ]


class T_SshTransHold(NeoTestTarpit):
    TARPIT = tarpitd.SshTransHoldTarpit

    TEST_SET: list[TarpitTestSet] = [
        TarpitTestSet(request=b"BAD_", excepted_response=b"SSH-"),
    ]


class T_SshEndless(NeoTestTarpit):
    TARPIT = tarpitd.SshEndlessTarpit

    TEST_SET: list[TarpitTestSet] = []

    async def have_lines(self, reader: asyncio.StreamReader, writer):
        for i in range(2):
            data = await read_with_timeout(reader, 64, 8)
            self.assertIn(b"\r\n", data)

    def _setup(self):
        self.TEST_SET.append(
            TarpitTestSet(request=b"SSH-FAKE\r\n", excepted_response=self.have_lines)
        )


if __name__ == "__main__":
    unittest.main()
