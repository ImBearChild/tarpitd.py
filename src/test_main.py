import unittest
import asyncio
import random
import tarpitd
import socket


class TestTarpit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        pass

    def create_tarpit_obj(self):
        pass

    async def asyncSetUp(self):
        print("[TEST] set up test")
        pit = self.create_tarpit_obj()
        self.port = random.randrange(50000,60000)
        self.server = await pit.create_server("127.0.0.1",self.port)
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
        return tarpitd.EchoTarpit(rate_limit=0)

    async def test_response(self):
        reader , writer = await asyncio.open_connection("127.0.0.1", self.port)
        writer.write(b"Aminoac\n")
        await writer.drain()
        p = await reader.readline()
        self.assertEqual(p, b"Aminoac\n")
        writer.close()
        await writer.wait_closed()
        self.addAsyncCleanup(self.on_cleanup)
        pass

class TestHttpTarpit(TestTarpit):
    def create_tarpit_obj(self):
        t = tarpitd.HttpOkTarpit(rate_limit=0)
        return t

    async def test_response(self):
        reader , writer = await asyncio.open_connection("127.0.0.1", self.port)
        line = await reader.readline()
        self.assertTrue(line.startswith(b"HTTP"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        self.addAsyncCleanup(self.on_cleanup)

if __name__ == '__main__':
    unittest.main()