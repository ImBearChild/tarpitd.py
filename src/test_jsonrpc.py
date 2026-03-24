import asyncio
import json
import unittest
import typing
import os
import tempfile

import tarpitd as jsonrpc 


class TestJsonRpcClient(unittest.TestCase):
    def setUp(self):
        self.client = jsonrpc.JsonRpcClient()

    def test_make_request_with_positional_params(self):
        payload = self.client.make_request("add", [1, 2])
        request = json.loads(payload)

        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertEqual(request["method"], "add")
        self.assertEqual(request["params"], [1, 2])
        self.assertEqual(request["id"], 1)

    def test_make_request_with_keyword_params(self):
        payload = self.client.make_request("add", {"a": 1, "b": 2})
        request = json.loads(payload)

        self.assertEqual(request["params"], {"a": 1, "b": 2})

    def test_make_request_without_params(self):
        payload = self.client.make_request("ping")
        request = json.loads(payload)

        self.assertNotIn("params", request)
        self.assertEqual(request["id"], 1)

    def test_make_notification(self):
        payload = self.client.make_notification("fire_and_forget", [1, 2])
        request = json.loads(payload)

        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertEqual(request["method"], "fire_and_forget")
        self.assertEqual(request["params"], [1, 2])
        self.assertNotIn("id", request)

    def test_make_batch(self):
        requests = [("add", [1, 2]), ("sub", [5, 3])]
        payload = self.client.make_batch(requests)
        batch = json.loads(payload)

        self.assertEqual(len(batch), 2)
        self.assertEqual(batch[0]["method"], "add")
        self.assertEqual(batch[1]["method"], "sub")
        self.assertEqual(batch[0]["id"], 1)
        self.assertEqual(batch[1]["id"], 2)

    def test_parse_success_response(self):
        self.client.make_request("add", [1, 2])
        response_data = {"jsonrpc": "2.0", "id": 1, "result": 3}
        result = self.client.parse_response(json.dumps(response_data))

        self.assertEqual(result["result"], 3)

    def test_parse_error_response(self):
        self.client.make_request("fail", [])
        response_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        }

        with self.assertRaises(jsonrpc.JsonRpcError) as ctx:
            self.client.parse_response(json.dumps(response_data))

        self.assertEqual(ctx.exception.code, -32601)

    def test_parse_batch_response(self):
        self.client.make_batch([("add", [1]), ("add", [2])])
        response_data = [
            {"jsonrpc": "2.0", "id": 1, "result": 2},
            {"jsonrpc": "2.0", "id": 2, "result": 3},
        ]
        result = self.client.parse_response(json.dumps(response_data))

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["result"], 2)

    def test_parse_error_clears_pending(self):
        self.client.make_request("test", [])
        self.assertEqual(self.client.get_pending_count(), 1)

        response_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32000, "message": "Error"},
        }
        try:
            self.client.parse_response(json.dumps(response_data))
        except jsonrpc.JsonRpcError:
            pass

        self.assertEqual(self.client.get_pending_count(), 0)

    def test_parse_success_clears_pending(self):
        self.client.make_request("test", [])
        self.assertEqual(self.client.get_pending_count(), 1)

        response_data = {"jsonrpc": "2.0", "id": 1, "result": "ok"}
        self.client.parse_response(json.dumps(response_data))

        self.assertEqual(self.client.get_pending_count(), 0)

    def test_invalid_json_raises(self):
        with self.assertRaises(jsonrpc.JsonRpcError) as ctx:
            self.client.parse_response("not json")

        self.assertEqual(ctx.exception.code, -32700)

    def test_invalid_response_format(self):
        with self.assertRaises(jsonrpc.JsonRpcError) as ctx:
            self.client.parse_response(json.dumps(123))

        self.assertEqual(ctx.exception.code, -32600)

    def test_wrong_version(self):
        with self.assertRaises(jsonrpc.JsonRpcError) as ctx:
            self.client.parse_response(
                json.dumps({"jsonrpc": "1.0", "id": 1, "result": 1})
            )

        self.assertEqual(ctx.exception.code, -32600)

    def test_notification_response_ignored(self):
        self.client.make_notification("notify", [])
        response_data = {"jsonrpc": "2.0", "method": "callback"}
        result = self.client.parse_response(json.dumps(response_data))

        self.assertIsNone(result)

    def test_incrementing_ids(self):
        payload1 = self.client.make_request("test", [])
        payload2 = self.client.make_request("test", [])

        req1 = json.loads(payload1)
        req2 = json.loads(payload2)

        self.assertEqual(req1["id"], 1)
        self.assertEqual(req2["id"], 2)

    def test_clear_pending(self):
        self.client.make_request("test1", [])
        self.client.make_request("test2", [])
        self.assertEqual(self.client.get_pending_count(), 2)

        self.client.clear_pending()
        self.assertEqual(self.client.get_pending_count(), 0)

    def test_bytes_input(self):
        self.client.make_request("echo", ["hello"])
        response_data = b'{"jsonrpc": "2.0", "id": 1, "result": "hello"}'
        result = self.client.parse_response(response_data)

        self.assertEqual(result["result"], "hello")


class TestJsonRpcError(unittest.TestCase):
    def test_error_to_dict(self):
        error = jsonrpc.JsonRpcError(-32601, "Method not found")
        error_dict = error.to_dict()

        self.assertEqual(error_dict["code"], -32601)
        self.assertEqual(error_dict["message"], "Method not found")
        self.assertNotIn("data", error_dict)

    def test_error_with_data(self):
        error = jsonrpc.JsonRpcError(-32000, "Server error", {"details": "extra info"})
        error_dict = error.to_dict()

        self.assertEqual(error_dict["data"], {"details": "extra info"})


class TestJsonRpcServer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.server = jsonrpc.JsonRpcServer()

    async def test_register_and_call_method(self):
        @self.server.register_method("add")
        async def add(a: int, b: int) -> int:
            return a + b

        request = {"jsonrpc": "2.0", "method": "add", "params": [2, 3], "id": 1}
        response = await self.server.handle_request(json.dumps(request))

        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["result"], 5)

    async def test_keyword_params(self):
        @self.server.register_method("greet")
        async def greet(name: str) -> str:
            return f"Hello, {name}"

        request = {
            "jsonrpc": "2.0",
            "method": "greet",
            "params": {"name": "World"},
            "id": 2,
        }
        response = await self.server.handle_request(json.dumps(request))

        self.assertEqual(response["result"], "Hello, World")

    async def test_notification_no_response(self):
        @self.server.register_method("notify")
        async def notify() -> None:
            pass

        request = {"jsonrpc": "2.0", "method": "notify", "params": []}
        response = await self.server.handle_request(json.dumps(request))

        self.assertIsNone(response)

    async def test_parse_error(self):
        response = await self.server.handle_request("not valid json")

        self.assertEqual(response["error"]["code"], -32700)
        self.assertIn("Parse error", response["error"]["message"])

    async def test_invalid_request_missing_jsonrpc(self):
        request = {"method": "test", "id": 1}
        response = await self.server.handle_request(json.dumps(request))

        self.assertEqual(response["error"]["code"], -32600)
        self.assertEqual(response["error"]["message"], "Invalid Request")

    async def test_invalid_request_missing_method(self):
        request = {"jsonrpc": "2.0", "id": 1}
        response = await self.server.handle_request(json.dumps(request))

        self.assertEqual(response["error"]["code"], -32600)

    async def test_method_not_found(self):
        request = {"jsonrpc": "2.0", "method": "nonexistent", "params": [], "id": 3}
        response = await self.server.handle_request(json.dumps(request))

        self.assertEqual(response["error"]["code"], -32601)
        self.assertIn("nonexistent", response["error"]["message"])

    async def test_handler_exception(self):
        @self.server.register_method("fail")
        async def fail() -> None:
            raise ValueError("intentional error")

        request = {"jsonrpc": "2.0", "method": "fail", "params": [], "id": 4}
        response = await self.server.handle_request(json.dumps(request))

        self.assertEqual(response["error"]["code"], -32000)
        self.assertIn("intentional error", response["error"]["message"])

    async def test_batch_requests(self):
        @self.server.register_method("double")
        async def double(x: int) -> int:
            return x * 2

        requests = [
            {"jsonrpc": "2.0", "method": "double", "params": [2], "id": 1},
            {"jsonrpc": "2.0", "method": "double", "params": [3], "id": 2},
        ]
        response = await self.server.handle_request(json.dumps(requests))

        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]["result"], 4)
        self.assertEqual(response[1]["result"], 6)

    async def test_batch_with_notification(self):
        @self.server.register_method("echo")
        async def echo(x: int) -> int:
            return x

        requests = [
            {"jsonrpc": "2.0", "method": "echo", "params": [1], "id": 1},
            {"jsonrpc": "2.0", "method": "echo", "params": [2]},
        ]
        response = await self.server.handle_request(json.dumps(requests))

        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["result"], 1)

    async def test_empty_batch(self):
        response = await self.server.handle_request(json.dumps([]))
        self.assertIsNone(response)

    async def test_batch_all_notifications(self):
        @self.server.register_method("noop")
        async def noop() -> None:
            pass

        requests = [
            {"jsonrpc": "2.0", "method": "noop", "params": []},
            {"jsonrpc": "2.0", "method": "noop", "params": []},
        ]
        response = await self.server.handle_request(json.dumps(requests))
        self.assertIsNone(response)

    async def test_get_method_names(self):
        @self.server.register_method("method_a")
        async def method_a() -> None:
            pass

        @self.server.register_method("method_b")
        async def method_b() -> None:
            pass

        names = self.server.get_method_names()
        self.assertIn("method_a", names)
        self.assertIn("method_b", names)
        self.assertEqual(len(names), 2)

    async def test_wrong_jsonrpc_version(self):
        @self.server.register_method("test")
        async def test() -> int:
            return 1

        request = {"jsonrpc": "1.0", "method": "test", "params": [], "id": 1}
        response = await self.server.handle_request(json.dumps(request))

        self.assertEqual(response["error"]["code"], -32600)

    async def test_bytes_input(self):
        @self.server.register_method("sum")
        async def sum_vals(a: int, b: int) -> int:
            return a + b

        request = {"jsonrpc": "2.0", "method": "sum", "params": [10, 20], "id": 5}
        response = await self.server.handle_request(json.dumps(request).encode("utf-8"))

        self.assertEqual(response["result"], 30)


class TestJsonRpcServerErrors(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.server = jsonrpc.JsonRpcServer()

    async def test_non_dict_request(self):
        response = await self.server.handle_request(json.dumps(123))
        self.assertEqual(response["error"]["code"], -32600)

    async def test_invalid_method_type(self):
        request = {"jsonrpc": "2.0", "method": 123, "id": 1}
        response = await self.server.handle_request(json.dumps(request))
        self.assertEqual(response["error"]["code"], -32600)


class TestJsonRpcUnixServer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.socket_path = os.path.join(self.temp_dir, "test.sock")
        self.server = jsonrpc.JsonRpcUnixServer(self.socket_path)

        @self.server.register_method("echo")
        async def echo(message: str) -> str:
            return message

        @self.server.register_method("add")
        async def add(a: int, b: int) -> int:
            return a + b

        await self.server.start()

    async def asyncTearDown(self):
        await self.server.stop()
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError:
                pass
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass

    async def _handle_request_async(self, request_data: str) -> typing.Any:
        """Helper to send request to server and get response."""
        reader, writer = await asyncio.open_unix_connection(path=self.socket_path)
        try:
            writer.write(request_data.encode("utf-8"))
            await writer.drain()
            data = await reader.read(65536)
            return json.loads(data.decode("utf-8")) if data else None
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def test_unix_server_echo(self):
        request = {"jsonrpc": "2.0", "method": "echo", "params": ["hello"], "id": 1}
        response = await self._handle_request_async(json.dumps(request))
        self.assertEqual(response["result"], "hello")

    async def test_unix_server_add(self):
        request = {"jsonrpc": "2.0", "method": "add", "params": [2, 3], "id": 1}
        response = await self._handle_request_async(json.dumps(request))
        self.assertEqual(response["result"], 5)

    async def test_unix_server_keyword_params(self):
        request = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"message": "world"},
            "id": 1,
        }
        response = await self._handle_request_async(json.dumps(request))
        self.assertEqual(response["result"], "world")

    async def test_unix_server_notification(self):
        request = {"jsonrpc": "2.0", "method": "echo", "params": ["test"]}
        response = await self._handle_request_async(json.dumps(request))
        self.assertIsNone(response)

    async def test_unix_server_batch(self):
        requests = [
            {"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": 1},
            {"jsonrpc": "2.0", "method": "add", "params": [3, 4], "id": 2},
        ]
        response = await self._handle_request_async(json.dumps(requests))
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]["result"], 3)
        self.assertEqual(response[1]["result"], 7)


if __name__ == "__main__":
    unittest.main()
