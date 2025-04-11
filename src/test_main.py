import unittest
import asyncio
import tarpitd
import time
import socket
import random


async def find_available_port(start_port, end_port, host="127.0.0.2"):
    while True:
        port = random.randrange(start=start_port,stop=end_port)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                s.close()
                #await asyncio.sleep(1)
                return port
        except socket.error as e:
            raise e
            pass
    return None


class TestTarpit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        pass

    def create_tarpit_obj(self):
        pass

    async def asyncSetUp(self):
        print("[TEST] set up test")
        pit = self.create_tarpit_obj()
        self.port = await find_available_port(50000, 60000)
        self.server = await pit.create_server("127.0.0.2", self.port)
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


class TestEchoTarpit(TestTarpit):
    def create_tarpit_obj(self):
        return tarpitd.EchoTarpit(rate_limit=0, client_trace=True)

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        writer.write(b"Aminoac\n")
        await writer.drain()
        p = await reader.readline()
        self.assertEqual(p, b"Aminoac\n")
        writer.close()
        await writer.wait_closed()
        self.addAsyncCleanup(self.on_cleanup)
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


class TestHttpOkTarpit(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.HttpOkTarpit(rate_limit=0)
        return t

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        line = await reader.readline()
        self.assertTrue(line.startswith(b"HTTP"))
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
        line = await reader.read(8)
        self.assertTrue(line.startswith(b"\x16\x03\x03"))
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
