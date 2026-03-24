"""Unit tests for EventStore and supervisor functionality."""

import unittest
import time
import tempfile
import os

import tarpitd


class TestEventStore(unittest.TestCase):
    """Test suite for EventStore class."""

    def setUp(self):
        """Create a fresh in-memory EventStore for each test."""
        self.store = tarpitd.EventStore(db_path=":memory:")

    def tearDown(self):
        """Close the EventStore after each test."""
        self.store.close()

    def _create_mock_conn_event(
        self,
        ev_type,
        tarpit_name="test_tarpit",
        tarpit_pattern="test_pattern",
        peername=("192.168.1.1", 12345),
        sockname=("127.0.0.1", 8080),
        metadata=None,
    ):
        """Create a mock ConnEvent for testing."""
        return tarpitd.ConnEvent(
            time=time.time(),
            ev_type=ev_type,
            tarpit_name=tarpit_name,
            tarpit_pattern=tarpit_pattern,
            peername=peername,
            sockname=sockname,
            metadata=metadata,
        )

    def test_init_in_memory(self):
        """Test EventStore initialization with in-memory database."""
        self.assertEqual(self.store.get_backend(), "memory")
        self.assertEqual(self.store.get_max_size(), 8 * 1024 * 1024)
        self.assertEqual(self.store.get_count(), 0)

    def test_init_disk(self):
        """Test EventStore initialization with disk-based database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            tmp_path = tmp.name

        try:
            store = tarpitd.EventStore(db_path=tmp_path)
            self.assertEqual(store.get_backend(), "disk")
            self.assertEqual(store.get_count(), 0)
            store.close()
        finally:
            os.unlink(tmp_path)

    def test_init_custom_size(self):
        """Test EventStore initialization with custom size limit."""
        store = tarpitd.EventStore(
            db_path=":memory:", max_size_bytes=1024 * 1024
        )
        self.assertEqual(store.get_max_size(), 1024 * 1024)
        store.close()

    def test_append_single_event(self):
        """Test appending a single event."""
        event = self._create_mock_conn_event("conn_open")
        self.store.append(event)

        self.assertEqual(self.store.get_count(), 1)

    def test_append_multiple_events(self):
        """Test appending multiple events."""
        for i in range(10):
            event = self._create_mock_conn_event(
                ev_type="conn_open",
                peername=(f"192.168.1.{i}", 12345 + i),
            )
            self.store.append(event)

        self.assertEqual(self.store.get_count(), 10)

    def test_query_basic(self):
        """Test basic query functionality."""
        # Add 5 events
        for i in range(5):
            event = self._create_mock_conn_event(
                ev_type="conn_open",
                tarpit_name=f"tarpit_{i}",
            )
            self.store.append(event)

        # Query all events
        results = self.store.query(start=1, end=5)
        self.assertEqual(len(results), 5)

    def test_query_range_forward(self):
        """Test querying events in forward order."""
        for i in range(10):
            event = self._create_mock_conn_event(
                ev_type="conn_open",
                tarpit_name=f"tarpit_{i}",
            )
            self.store.append(event)

        # Query events 3-7 (inclusive)
        results = self.store.query(start=3, end=7)
        self.assertEqual(len(results), 5)

        # Check ordering (should be ascending by id)
        for i, result in enumerate(results):
            self.assertEqual(result["tarpit_name"], f"tarpit_{i + 2}")

    def test_query_range_reverse(self):
        """Test querying events in reverse order."""
        for i in range(10):
            event = self._create_mock_conn_event(
                ev_type="conn_open",
                tarpit_name=f"tarpit_{i}",
            )
            self.store.append(event)

        # Query last 3 events in reverse order
        results = self.store.query(start=10, end=8)
        self.assertEqual(len(results), 3)

        # Check ordering (should be descending)
        self.assertEqual(results[0]["tarpit_name"], "tarpit_9")
        self.assertEqual(results[1]["tarpit_name"], "tarpit_8")
        self.assertEqual(results[2]["tarpit_name"], "tarpit_7")

    def test_query_negative_indices(self):
        """Test querying with negative indices."""
        for i in range(10):
            event = self._create_mock_conn_event(
                ev_type="conn_open",
                tarpit_name=f"tarpit_{i}",
            )
            self.store.append(event)

        # Query last 3 events using negative indices
        results = self.store.query(start=-3, end=-1)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["tarpit_name"], "tarpit_7")
        self.assertEqual(results[1]["tarpit_name"], "tarpit_8")
        self.assertEqual(results[2]["tarpit_name"], "tarpit_9")

    def test_query_filter_by_peer_ip_exact(self):
        """Test filtering events by exact peer IP match."""
        ips = ["192.168.1.1", "192.168.1.2", "192.168.1.1", "10.0.0.1"]
        for i, ip in enumerate(ips):
            event = self._create_mock_conn_event(
                ev_type="conn_open",
                peername=(ip, 12345),
            )
            self.store.append(event)

        # Filter by exact IP
        results = self.store.query(peer_ip="192.168.1.1")
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result["peer_ip"], "192.168.1.1")

    def test_query_filter_by_peer_ip_wildcard(self):
        """Test filtering events by peer IP with wildcard."""
        ips = ["192.168.1.1", "192.168.1.2", "192.168.2.1", "10.0.0.1"]
        for ip in ips:
            event = self._create_mock_conn_event(
                ev_type="conn_open",
                peername=(ip, 12345),
            )
            self.store.append(event)

        # Filter using wildcard
        results = self.store.query(peer_ip="192.168.1.*")
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result["peer_ip"].startswith("192.168.1."))

    def test_query_filter_by_tarpit_name(self):
        """Test filtering events by tarpit name."""
        names = ["ssh_tarpit", "http_tarpit", "ssh_tarpit"]
        for name in names:
            event = self._create_mock_conn_event(
                ev_type="conn_open",
                tarpit_name=name,
            )
            self.store.append(event)

        # Filter by tarpit name
        results = self.store.query(tarpit_name="ssh_tarpit")
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result["tarpit_name"], "ssh_tarpit")

    def test_query_filter_by_ev_type(self):
        """Test filtering events by event type."""
        types = ["conn_open", "conn_close", "conn_open", "conn_error"]
        for ev_type in types:
            event = self._create_mock_conn_event(ev_type=ev_type)
            self.store.append(event)

        # Filter by event type
        results = self.store.query(ev_type="conn_open")
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result["ev_type"], "conn_open")

    def test_query_filter_combined(self):
        """Test combining multiple filters."""
        for i in range(10):
            event = self._create_mock_conn_event(
                ev_type="conn_open" if i % 2 == 0 else "conn_close",
                tarpit_name="tarpit_a" if i < 5 else "tarpit_b",
                peername=(f"192.168.{i % 2}.1", 12345),
            )
            self.store.append(event)

        # Filter by multiple criteria
        results = self.store.query(
            ev_type="conn_open",
            tarpit_name="tarpit_a",
            peer_ip="192.168.0.1",
        )
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result["ev_type"], "conn_open")
            self.assertEqual(result["tarpit_name"], "tarpit_a")
            self.assertEqual(result["peer_ip"], "192.168.0.1")

    def test_query_empty_result(self):
        """Test querying with no matching results."""
        event = self._create_mock_conn_event(ev_type="conn_open")
        self.store.append(event)

        # Query with filter that won't match
        results = self.store.query(ev_type="nonexistent")
        self.assertEqual(len(results), 0)

    def test_query_invalid_catalog(self):
        """Test querying with invalid catalog raises error."""
        with self.assertRaises(ValueError) as ctx:
            self.store.query(catalog="invalid_catalog")
        self.assertIn("Unknown catalog", str(ctx.exception))

    def test_get_count_empty(self):
        """Test get_count on empty store."""
        self.assertEqual(self.store.get_count(), 0)
        self.assertEqual(self.store.get_count("events"), 0)

    def test_get_count_invalid_catalog(self):
        """Test get_count with invalid catalog raises error."""
        with self.assertRaises(ValueError) as ctx:
            self.store.get_count("invalid_catalog")
        self.assertIn("Unknown catalog", str(ctx.exception))

    def test_get_size_empty(self):
        """Test get_size on empty store."""
        size = self.store.get_size()
        self.assertIsInstance(size, int)
        self.assertGreaterEqual(size, 0)

    def test_get_size_grows_with_events(self):
        """Test that database size grows with more events."""
        size_before = self.store.get_size()

        # Add many events
        for _ in range(100):
            event = self._create_mock_conn_event(ev_type="conn_open")
            self.store.append(event)

        size_after = self.store.get_size()
        self.assertGreater(size_after, size_before)

    def test_get_backend(self):
        """Test get_backend returns correct value."""
        self.assertEqual(self.store.get_backend(), "memory")

    def test_get_max_size(self):
        """Test get_max_size returns correct value."""
        self.assertEqual(self.store.get_max_size(), 8 * 1024 * 1024)

    def test_append_with_metadata(self):
        """Test appending event with metadata."""
        event = self._create_mock_conn_event(
            ev_type="conn_open",
            metadata={"key": "value", "number": 42},
        )
        self.store.append(event)

        results = self.store.query()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metadata"], {"key": "value", "number": 42})

    def test_append_without_metadata(self):
        """Test appending event without metadata."""
        event = self._create_mock_conn_event(
            ev_type="conn_open",
            metadata=None,
        )
        self.store.append(event)

        results = self.store.query()
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]["metadata"])

    def test_query_limit_and_offset(self):
        """Test query respects limit and offset."""
        for i in range(20):
            event = self._create_mock_conn_event(
                ev_type="conn_open",
                tarpit_name=f"tarpit_{i}",
            )
            self.store.append(event)

        # Query with range
        results = self.store.query(start=5, end=10)
        self.assertEqual(len(results), 6)
        self.assertEqual(results[0]["tarpit_name"], "tarpit_4")
        self.assertEqual(results[5]["tarpit_name"], "tarpit_9")


if __name__ == "__main__":
    unittest.main()
