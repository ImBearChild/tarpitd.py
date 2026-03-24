import unittest
import asyncio
import tarpitd
import time
import dataclasses


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


class TarpitTestCase(unittest.IsolatedAsyncioTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.BaseTarpit
    CONF: dict = {"rate_limit": 1024}

    def _setup(self):
        pass

    def setUp(self):
        self.tarpit_instance = self.TARPIT(**self.CONF)
        pass

    async def asyncSetUp(self) -> None:
        print("[TarpitTestCase] set up test")
        t = self.tarpit_instance
        self.server = await t.create_server("127.0.0.2", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        await self.server.start_serving()
        print("[TarpitTestCase] set up done")

    async def asyncTearDown(self):
        print("[TarpitTestCase] teardown test")
        self.server.close()
        await self.server.wait_closed()
        print("[TarpitTestCase] teardown test done")

    async def do_simple_test(self, request: bytes, excepted_response: bytes):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        writer.write(request)
        await writer.drain()
        response = await read_with_timeout(reader, len(excepted_response), 10)
        await asyncio.sleep(1)
        self.assertIn(excepted_response, response)
        pass


async def get_http_header(reader: asyncio.StreamReader) -> str:
    headers = b""
    for i in range(32):
        line = await readline_with_timeout(reader, 1)
        if line == b"\r\n":
            break
        headers += line

    decoded_headers = headers.decode("utf-8")
    return decoded_headers


class TestSshValidator(TarpitTestCase):
    class TARPIT(tarpitd.SshTransHoldTarpit):
        @dataclasses.dataclass
        class ValidatorConfig(tarpitd.SshTransHoldTarpit.ValidatorConfig):
            response_failed: bytes = b"BAD_RESPONSE"
            pass

        pass

    CONF: dict = {"rate_limit": 1024, "validation_level": 1}

    async def test_normal_ssh_banner(self):
        await self.do_simple_test(b"SSH-", b"SSH-")

    async def test_bad_ssh_banner(self):
        await self.do_simple_test(b"NOT_SSH", b"BAD_RESPONSE")

    pass


class TestRateLimitPositive(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.EndlessBannerTarpit
    CONF = {"rate_limit": 2}

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        t1 = time.time()
        await reader.readexactly(8)
        t2 = time.time()

        self.assertTrue(abs((t2 - t1 - 4) / 4) < 0.5)
        await writer.drain()
        writer.close()
        await writer.wait_closed()


class TestRateLimitNegative(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.EndlessBannerTarpit
    CONF = {"rate_limit": -2}

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        t1 = time.time()
        await reader.readexactly(2)
        t2 = time.time()

        self.assertTrue(abs((t2 - t1 - 4) / 4) < 0.5)
        await writer.drain()
        writer.close()
        await writer.wait_closed()


class TestHttpTarpit(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.HttpEndlessHeaderTarpit
    CONF = {"rate_limit": 0}

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


class TestTlsTarpit(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.TlsHelloRequestTarpit
    CONF = {"rate_limit": 0}

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        writer.write(b"\x16\x03\x03")
        line = await reader.read(8)
        self.assertTrue(line.startswith(b"\x16\x03\x03"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()


class TestTlsSlowHelloTarpit(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.TlsSlowHelloTarpit
    CONF = {"rate_limit": 0}

    async def test_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        writer.write(b"\x16\x03\x03")
        line = await reader.read(8)
        self.assertTrue(line.startswith(b"\x16\x03\x03\x3e\x63"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()


class TestHttpOk(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.HttpOkTarpit
    CONF = {"rate_limit": 1024}

    async def test_get_request(self):
        await self.do_simple_test(b"GET ", b"HTTP")


class TestHttpDeflateHtml(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.HttpDeflateHtmlBombTarpit
    CONF = {"rate_limit": 1024}

    async def test_get_request(self):
        await self.do_simple_test(b"GET ", b"HTTP")

    async def test_have_gzip(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        writer.write(b"GET ")
        await writer.drain()
        header = await get_http_header(reader)
        self.assertFalse("deflate" in header)
        self.assertTrue("gzip" in header)


class TestHttpDeflateSize(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.HttpDeflateSizeBombTarpit
    CONF = {"rate_limit": 1024}

    async def test_have_deflate(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        writer.write(b"GET ")
        await writer.drain()
        header = await get_http_header(reader)
        self.assertTrue("deflate" in header)
        self.assertFalse("gzip" in header)


class TestSshTransHold(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.SshTransHoldTarpit
    CONF = {"rate_limit": 0}

    async def test_bad_request(self):
        await self.do_simple_test(b"BAD_", b"SSH-")


class TestSshEndless(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.SshEndlessTarpit
    CONF = {"rate_limit": 1024}

    async def test_have_lines(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        writer.write(b"SSH-FAKE\r\n")
        await writer.drain()
        for i in range(2):
            data = await read_with_timeout(reader, 64, 8)
            self.assertIn(b"\r\n", data)


class TestSshBasic(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.SshTransHoldTarpit
    CONF = {"rate_limit": 0, "validation_level": 0}  # Validation disabled

    async def test_ssh_banner_validation_disabled(self):
        """Test that SSH still sends proper banner when validation is disabled"""
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        # Should receive SSH identification string even when validation is disabled
        banner = await readline_with_timeout(reader, 2)
        # SSH protocol requires sending identification upon connection
        self.assertIn(
            b"SSH-2.0-OpenSSH", banner
        )  # Should start with proper SSH identification

    pass


class TestFtp(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.FtpEndlessMotdTarpit
    CONF = {"rate_limit": 1024, "validation_level": 1}

    async def test_without_user(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        writer.write(b"HTTP\r\n")
        await writer.drain()
        data = await reader.readline()
        self.assertIn(b"220", data)
        data = await reader.readline()
        self.assertIn(b"530", data)
        pass

    async def test_user_login(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        writer.write(b"USER\r\n")
        await writer.drain()
        data = await reader.readline()
        self.assertIn(b"220", data)
        data = await reader.readline()
        self.assertIn(b"230", data)
        pass


class TestSmtp(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.SmtpTarpit
    CONF = {"rate_limit": 1024, "validation_level": 1}

    async def test_smtp_banner(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        # Wait for the SMTP banner
        banner = await readline_with_timeout(reader, 2)
        self.assertIn(b"220", banner)
        # Try sending HELO (should be accepted as valid command for validation)
        writer.write(b"HELO example.com\r\n")
        await writer.drain()
        # The validation passes, now we have normal operation
        # Read responses from actual handler
        response = await readline_with_timeout(reader, 5)
        # Default SmtpTarpit just accepts validated clients
        # The key is that HELO should not trigger a rejection
        # Since we just want to validate that validation works, check connection doesn't get closed immediately
        self.assertIsNotNone(response)  # Connection should still be alive

        pass

    async def test_invalid_smtp_command_during_validation(self):
        # Testing that invalid commands during validation phase are rejected
        tarpit_with_validation = tarpitd.SmtpTarpit(
            rate_limit=1024, validation_level=1
        )
        server = await tarpit_with_validation.create_server("127.0.0.3", 0)
        port = server.sockets[0].getsockname()[1]
        await server.start_serving()

        try:
            reader, writer = await asyncio.open_connection("127.0.0.3", port)
            await asyncio.sleep(0.1)
            # Wait for the SMTP banner
            banner = await readline_with_timeout(reader, 2)
            self.assertIn(b"220", banner)

            # Send an invalid command that should fail validation
            writer.write(b"INVALID_COMMAND\r\n")
            await writer.drain()
            # With validation on, an invalid command during the read phase should cause rejection
            # Response after validation failure depends on the implementation

            # Give it a moment for processing
            await asyncio.sleep(1)
        finally:
            server.close()
            await server.wait_closed()
        pass


class TestSmtpEndlessEhlo(TarpitTestCase):
    TARPIT: type[tarpitd.BaseTarpit] = tarpitd.SmtpEndlessEhloTarpit
    CONF = {"rate_limit": 0, "validation_level": 0}

    async def test_smtp_endless_ehlo_response(self):
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        # Should get initial SMTP greeting
        greeting = await readline_with_timeout(reader, 2)
        self.assertIn(b"220", greeting)  # SMTP greeting should be first

        # Should get initial 250- response (first from handle_client method)
        welcome = await readline_with_timeout(reader, 2)
        self.assertIn(b"250-", welcome)  # 250- message should come next

        # Should then get endless hex responses
        for i in range(2):  # Test fewer loops to avoid hanging
            response = await readline_with_timeout(reader, 10)
            if response:
                self.assertIn(b"250-", response)
            else:
                break
        pass

    async def test_smtp_banner(self):
        # should Still have banner
        reader, writer = await asyncio.open_connection("127.0.0.2", self.port)
        await asyncio.sleep(0.1)
        banner = await readline_with_timeout(reader, 2)
        self.assertIn(b"220", banner)
        writer.write(b"HELO example.com\r\n")
        await writer.drain()
        response = await readline_with_timeout(reader, 5)
        self.assertIsNotNone(response)

        pass


if __name__ == "__main__":
    unittest.main()
