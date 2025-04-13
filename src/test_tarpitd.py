import unittest
import asyncio
import tarpitd
import time
import typing
import dataclasses


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


class TarpitEntry(typing.NamedTuple):
    port: int
    server: asyncio.Server


@dataclasses.dataclass
class TarpitsBeTested:
    default: TarpitEntry | None = None
    without_verify: TarpitEntry | None = None

class NeoTestTarpit(unittest.IsolatedAsyncioTestCase):
    TARPIT = tarpitd.BaseTarpit
    REQUEST = b""
    REQUEST_INVALID = b"NO_TEST!!!"
    CONFIG={'rate_limit':0}

    async def setup_tarpit(self, **conf):
        t = self.TARPIT()
        t_server = await t.create_server("127.0.0.2", 0)
        t_port = t_server.sockets[0].getsockname()[1]
        return TarpitEntry(t_port, t_server)

    async def asyncSetUp(self) -> None:
        print("[TEST] set up test")
        self.tarpits: TarpitsBeTested = TarpitsBeTested()
        self.tarpits.default = await self.setup_tarpit(**self.CONFIG)

        async with asyncio.TaskGroup() as tg:
            for i in dataclasses.fields(self.tarpits):
                if item := getattr(self.tarpits, i.name):
                    tg.create_task(item.server.start_serving())
        print("[TEST] set up done")

    async def asyncTearDown(self):
        print("[TEST] teardown test")
        for i in dataclasses.fields(self.tarpits):
            if item := getattr(self.tarpits, i.name):
                item.server.close()
                await item.server.wait_closed()
        print("[TEST] teardown test done")

    async def verify_response(self, reader: asyncio.StreamReader):
        raise NotImplementedError

    async def do_default_test(self):
        port = self.tarpits.default.port
        reader, writer = await asyncio.open_connection("127.0.0.2", port)
        writer.write(self.REQUEST)
        await writer.drain()
        await self.verify_response(reader)
        pass

    async def test(self):
        if self.__class__ is not NeoTestTarpit:
            await self.do_default_test()


class T_EchoTarpit(NeoTestTarpit):
    TARPIT = tarpitd.EchoTarpit
    REQUEST = b"TEST\n"

    async def verify_response(self, reader: asyncio.StreamReader):
        self.assertEqual(await reader.readline(), self.REQUEST)

class T_HttpTarpit(NeoTestTarpit):
    TARPIT = tarpitd.HttpOkTarpit
    REQUEST = b"GET \n"

    async def verify_response(self, reader: asyncio.StreamReader):
        self.assertTrue((await reader.readline()).startswith(b"HTTP"))



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


class TestHttpTarpitClientExamine(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.HttpEndlessHeaderTarpit(rate_limit=0, client_examine=True)
        return t

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        writer.write(b"HEAD")
        await writer.drain()
        line = await reader.readline()
        self.assertTrue(line.startswith(b"HTTP"))
        writer.close()
        await writer.wait_closed()
        while True:
            line = await reader.readline()
            if line.startswith(b"Set-Cookie:"):
                self.assertFalse(line.find(b"=") == -1)
                break
        self.addAsyncCleanup(self.on_cleanup)

    async def test_response_bad_req(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        writer.write(b"DUCK")
        await writer.drain()
        line = await reader.readline()
        self.assertTrue(len(line) == 0)
        self.addAsyncCleanup(self.on_cleanup)


class TestHttpDeflateSizeBombTarpit(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.HttpDeflateSizeBombTarpit(rate_limit=0)
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
            if line.startswith(b"Content-Encoding"):
                self.assertFalse(line.find(b"deflate") == -1)
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


class TestSshTarpit(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.SshTransHoldTarpit(rate_limit=0)
        return t

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        line = await reader.read(4)
        self.assertTrue(line.startswith(b"SSH"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        self.addAsyncCleanup(self.on_cleanup)


if __name__ == "__main__":
    unittest.main()
