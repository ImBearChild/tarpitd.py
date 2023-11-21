import unittest
import tarpitd
import asyncio
import random

events = []

async def run_server(ser):
    t = await ser
    await t.start_serving()
    

class TestTarpit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        events.append("setUp")

    def create_tarpit_obj(self):
        pass

    async def asyncSetUp(self):
        pit = self.create_tarpit_obj()
        self.port = random.randrange(50000,60000)
        self.server = await pit.create_server("127.0.0.1",self.port)
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.server.start_serving())
        events.append("asyncSetUp")

    def tearDown(self):
        events.append("tearDown")

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()
        try:
            loop = self.server.get_loop()
            loop.stop()
            loop.close()
        except Exception as e:
            pass
        events.append("asyncTearDown")

    async def on_cleanup(self):
        events.append("cleanup")

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
        pass

if __name__ == '__main__':
    unittest.main()