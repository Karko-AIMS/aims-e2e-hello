import argparse
import io
import json
import threading
import unittest

from simulator.send_hello import (
    GatewayProtocolError,
    build_payload,
    encode_message,
    parse_ack,
    parse_args,
    resolve_vehicle_ids,
    send_messages,
)


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.payloads = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        return None

    def send_hello(self, payload):
        self.payloads.append(payload)
        return self.responses.pop(0) if self.responses else "OK"


class RecordingClientFactory:
    def __init__(self, default_responses=None):
        self.default_responses = list(default_responses or ["OK"])
        self.clients = []
        self.lock = threading.Lock()

    def __call__(self, host, port, timeout):
        client = FakeClient(self.default_responses)
        with self.lock:
            self.clients.append(client)
        return client


class SendHelloTests(unittest.TestCase):
    def test_build_payload_sets_expected_hello_fields(self):
        payload = build_payload("VHC-001", "1.0.0", "2026-03-19T10:00:00+09:00")

        self.assertEqual(
            payload,
            {
                "type": "HELLO",
                "vehicle_id": "VHC-001",
                "firmware_version": "1.0.0",
                "timestamp": "2026-03-19T10:00:00+09:00",
            },
        )

    def test_encode_message_produces_newline_delimited_json(self):
        payload = build_payload("VHC-001", "1.0.0", "2026-03-19T10:00:00+09:00")

        encoded = encode_message(payload)

        self.assertTrue(encoded.endswith(b"\n"))
        self.assertEqual(json.loads(encoded.decode("utf-8")), payload)

    def test_parse_ack_accepts_known_gateway_responses(self):
        self.assertEqual(parse_ack(b"OK\n"), "OK")
        self.assertEqual(parse_ack(b"ERR\n"), "ERR")
        self.assertEqual(parse_ack(b"IGNORED\n"), "IGNORED")

    def test_parse_ack_rejects_empty_or_unknown_gateway_response(self):
        with self.assertRaises(GatewayProtocolError):
            parse_ack(b"")

        with self.assertRaises(GatewayProtocolError):
            parse_ack(b"WAT\n")

    def test_parse_args_applies_defaults(self):
        args = parse_args(["--vehicle-id", "VHC-001", "--firmware-version", "1.0.0"])

        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 9000)
        self.assertEqual(args.vehicle_id_prefix, None)
        self.assertEqual(args.vehicle_count, 1)
        self.assertEqual(args.count, 1)
        self.assertEqual(args.forever, False)
        self.assertEqual(args.interval, 0.0)
        self.assertEqual(args.timeout, 3.0)

    def test_parse_args_rejects_forever_without_positive_interval(self):
        with self.assertRaises(SystemExit):
            parse_args(["--vehicle-id", "VHC-001", "--firmware-version", "1.0.0", "--forever"])

    def test_parse_args_rejects_invalid_vehicle_count(self):
        with self.assertRaises(SystemExit):
            parse_args(
                ["--vehicle-id", "VHC-001", "--firmware-version", "1.0.0", "--vehicle-count", "0"]
            )

    def test_resolve_vehicle_ids_uses_prefix_for_multi_vehicle_mode(self):
        args = argparse.Namespace(vehicle_id="VHC", vehicle_id_prefix="CAR", vehicle_count=3)

        vehicle_ids = resolve_vehicle_ids(args)

        self.assertEqual(vehicle_ids, ["CAR-001", "CAR-002", "CAR-003"])

    def test_send_messages_repeats_and_waits_between_messages(self):
        client = FakeClient(["OK", "OK", "OK"])
        sleeps = []
        stdout = io.StringIO()
        stderr = io.StringIO()
        timestamps = iter(
            [
                "2026-03-19T10:00:00+09:00",
                "2026-03-19T10:00:01+09:00",
                "2026-03-19T10:00:02+09:00",
            ]
        )
        args = argparse.Namespace(
            host="127.0.0.1",
            port=9000,
            vehicle_id="VHC-001",
            vehicle_id_prefix=None,
            vehicle_count=1,
            firmware_version="1.0.0",
            timestamp=None,
            count=3,
            forever=False,
            interval=0.5,
            timeout=3.0,
        )

        exit_code = send_messages(
            args,
            client_factory=lambda host, port, timeout: client,
            timestamp_factory=lambda: next(timestamps),
            sleeper=lambda seconds: sleeps.append(seconds),
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual([payload["timestamp"] for payload in client.payloads], [
            "2026-03-19T10:00:00+09:00",
            "2026-03-19T10:00:01+09:00",
            "2026-03-19T10:00:02+09:00",
        ])
        self.assertEqual(sleeps, [0.5, 0.5])
        self.assertIn("[VHC-001 1/3] ACK OK", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_send_messages_fails_fast_on_non_ok_ack(self):
        client = FakeClient(["OK", "ERR", "OK"])
        stdout = io.StringIO()
        stderr = io.StringIO()
        args = argparse.Namespace(
            host="127.0.0.1",
            port=9000,
            vehicle_id="VHC-002",
            vehicle_id_prefix=None,
            vehicle_count=1,
            firmware_version="1.0.1",
            timestamp="2026-03-19T11:00:00+09:00",
            count=3,
            forever=False,
            interval=1.0,
            timeout=3.0,
        )

        exit_code = send_messages(
            args,
            client_factory=lambda host, port, timeout: client,
            sleeper=lambda seconds: None,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(len(client.payloads), 2)
        self.assertIn("gateway returned non-success ACK: ERR", stderr.getvalue())

    def test_send_messages_runs_forever_until_interrupted(self):
        client = FakeClient(["OK", "OK", "OK"])
        stdout = io.StringIO()
        stderr = io.StringIO()
        timestamps = iter(
            [
                "2026-03-19T12:00:00+09:00",
                "2026-03-19T12:00:01+09:00",
                "2026-03-19T12:00:02+09:00",
            ]
        )
        args = argparse.Namespace(
            host="127.0.0.1",
            port=9000,
            vehicle_id="VHC-003",
            vehicle_id_prefix=None,
            vehicle_count=1,
            firmware_version="1.0.2",
            timestamp=None,
            count=1,
            forever=True,
            interval=1.0,
            timeout=3.0,
        )

        sleep_calls = {"count": 0}

        def interrupting_sleep(seconds):
            sleep_calls["count"] += 1
            if sleep_calls["count"] >= 3:
                raise KeyboardInterrupt()

        exit_code = send_messages(
            args,
            client_factory=lambda host, port, timeout: client,
            timestamp_factory=lambda: next(timestamps),
            sleeper=interrupting_sleep,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 130)
        self.assertEqual(len(client.payloads), 3)
        self.assertIn("[VHC-003 1/forever] ACK OK", stdout.getvalue())
        self.assertIn("stopped by user", stderr.getvalue())

    def test_send_messages_simulates_multiple_vehicles_concurrently(self):
        client_factory = RecordingClientFactory()
        stdout = io.StringIO()
        stderr = io.StringIO()
        args = argparse.Namespace(
            host="127.0.0.1",
            port=9000,
            vehicle_id="VHC",
            vehicle_id_prefix=None,
            vehicle_count=3,
            firmware_version="1.0.0",
            timestamp="2026-03-19T13:00:00+09:00",
            count=1,
            forever=False,
            interval=0.0,
            timeout=3.0,
        )

        exit_code = send_messages(
            args,
            client_factory=client_factory,
            sleeper=lambda seconds: None,
            stdout=stdout,
            stderr=stderr,
        )

        sent_vehicle_ids = sorted(client.payloads[0]["vehicle_id"] for client in client_factory.clients)

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(client_factory.clients), 3)
        self.assertEqual(sent_vehicle_ids, ["VHC-001", "VHC-002", "VHC-003"])
        self.assertIn("[VHC-001 1/1] ACK OK", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
