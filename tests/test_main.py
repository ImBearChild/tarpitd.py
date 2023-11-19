import unittest
import tarpitd
import asyncio

events = []

async def run_server(ser):
    t = await ser
    await t.start_serving()
    

class TestStringMethods(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        events.append("setUp")

    async def asyncSetUp(self):
        pit = tarpitd.BaseTarpit(rate_limit=16)
        self.server = await pit.create_server("0.0.0.0",8888)
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.server.start_serving())
        events.append("asyncSetUp")

    async def test_response(self):
        reader , writer = await asyncio.open_connection("127.0.0.1",8888)
        writer.write(b"Aminoac\n")
        await writer.drain()
        p = await reader.readline()
        self.assertEqual(p, b"Aminoac\n")
        writer.close()
        await writer.wait_closed()
        self.addAsyncCleanup(self.on_cleanup)
        pass

    def tearDown(self):
        events.append("tearDown")

    async def asyncTearDown(self):
        loop = self.server.get_loop()
        loop.stop()
        events.append("asyncTearDown")

    async def on_cleanup(self):
        events.append("cleanup")


if __name__ == '__main__':
    unittest.main()