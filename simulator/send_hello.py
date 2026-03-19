#!/usr/bin/env python3
"""Send HELLO messages to the gateway TCP endpoint."""

from __future__ import annotations

import argparse
import json
import socket
import sys
import threading
import time
from datetime import datetime
from typing import Callable, TextIO


VALID_ACKS = {"OK", "ERR", "IGNORED"}


class GatewayProtocolError(RuntimeError):
    """Raised when the gateway response is missing or malformed."""


def iso_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def build_payload(vehicle_id: str, firmware_version: str, timestamp: str) -> dict[str, str]:
    return {
        "type": "HELLO",
        "vehicle_id": vehicle_id,
        "firmware_version": firmware_version,
        "timestamp": timestamp,
    }


def encode_message(payload: dict[str, str]) -> bytes:
    return f"{json.dumps(payload, separators=(',', ':'))}\n".encode("utf-8")


def parse_ack(raw_response: bytes) -> str:
    ack = raw_response.decode("utf-8").strip()
    if ack not in VALID_ACKS:
        raise GatewayProtocolError(f"unexpected gateway response: {ack or '<empty>'}")
    return ack


def write_line(stream: TextIO, lock: threading.Lock | None, message: str) -> None:
    if lock is None:
        stream.write(f"{message}\n")
        stream.flush()
        return

    with lock:
        stream.write(f"{message}\n")
        stream.flush()


class TcpHelloClient:
    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket | None = None

    def __enter__(self) -> "TcpHelloClient":
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        self.sock.settimeout(self.timeout)
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def send_hello(self, payload: dict[str, str]) -> str:
        if self.sock is None:
            raise RuntimeError("client is not connected")

        self.sock.sendall(encode_message(payload))
        response = self._recv_line()
        return parse_ack(response)

    def _recv_line(self) -> bytes:
        if self.sock is None:
            raise RuntimeError("client is not connected")

        chunks = bytearray()
        while True:
            chunk = self.sock.recv(1024)
            if not chunk:
                break

            chunks.extend(chunk)
            if b"\n" in chunk:
                break

        return bytes(chunks)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send HELLO messages to the AIMS gateway.")
    parser.add_argument("--host", default="127.0.0.1", help="Gateway host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=9000, help="Gateway TCP port. Default: 9000")
    parser.add_argument("--vehicle-id", required=True, help="Vehicle identifier")
    parser.add_argument(
        "--vehicle-id-prefix",
        help="Vehicle ID prefix to use when simulating multiple vehicles",
    )
    parser.add_argument(
        "--vehicle-count",
        type=int,
        default=1,
        help="Number of simultaneous vehicles to simulate",
    )
    parser.add_argument("--firmware-version", required=True, help="Vehicle firmware version")
    parser.add_argument(
        "--timestamp",
        help="Override timestamp for every message. Default: current local ISO-8601 time",
    )
    parser.add_argument("--count", type=int, default=1, help="Number of HELLO messages to send")
    parser.add_argument(
        "--forever",
        action="store_true",
        help="Send HELLO messages continuously until interrupted",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.0,
        help="Seconds to wait between messages",
    )
    parser.add_argument("--timeout", type=float, default=3.0, help="Socket timeout in seconds")
    args = parser.parse_args(argv)

    if args.count < 1:
        parser.error("--count must be at least 1")

    if args.vehicle_count < 1:
        parser.error("--vehicle-count must be at least 1")

    if args.interval < 0:
        parser.error("--interval must be greater than or equal to 0")

    if args.timeout <= 0:
        parser.error("--timeout must be greater than 0")

    if args.forever and args.interval <= 0:
        parser.error("--forever requires --interval greater than 0")

    return args


def resolve_vehicle_ids(args: argparse.Namespace) -> list[str]:
    vehicle_count = getattr(args, "vehicle_count", 1)
    vehicle_id_prefix = getattr(args, "vehicle_id_prefix", None)

    if vehicle_count == 1:
        return [args.vehicle_id]

    prefix = vehicle_id_prefix or args.vehicle_id
    width = max(3, len(str(vehicle_count)))
    return [f"{prefix}-{index:0{width}d}" for index in range(1, vehicle_count + 1)]


def send_vehicle_messages(
    args: argparse.Namespace,
    vehicle_id: str,
    *,
    client_factory: Callable[[str, int, float], TcpHelloClient],
    timestamp_factory: Callable[[], str],
    sleeper: Callable[[float], None],
    stdout: TextIO,
    stderr: TextIO,
    io_lock: threading.Lock | None = None,
    stop_event: threading.Event | None = None,
    start_barrier: threading.Barrier | None = None,
) -> int:
    stop_event = stop_event or threading.Event()
    total_label = args.count if not args.forever else "forever"

    try:
        with client_factory(args.host, args.port, args.timeout) as client:
            if start_barrier is not None:
                start_barrier.wait(timeout=args.timeout)

            index = 0
            while not stop_event.is_set():
                timestamp = args.timestamp or timestamp_factory()
                payload = build_payload(vehicle_id, args.firmware_version, timestamp)
                write_line(
                    stdout,
                    io_lock,
                    f"[{vehicle_id} {index + 1}/{total_label}] SEND "
                    f"firmware_version={payload['firmware_version']} timestamp={payload['timestamp']}",
                )

                ack = client.send_hello(payload)
                write_line(stdout, io_lock, f"[{vehicle_id} {index + 1}/{total_label}] ACK {ack}")

                if ack != "OK":
                    write_line(stderr, io_lock, f"{vehicle_id} gateway returned non-success ACK: {ack}")
                    stop_event.set()
                    return 1

                index += 1

                if not args.forever and index >= args.count:
                    break

                if args.interval > 0:
                    sleeper(args.interval)
    except KeyboardInterrupt:
        stop_event.set()
        write_line(stderr, io_lock, "stopped by user")
        return 130
    except threading.BrokenBarrierError:
        stop_event.set()
        return 1
    except (OSError, ValueError, GatewayProtocolError) as error:
        stop_event.set()
        if start_barrier is not None:
            start_barrier.abort()
        write_line(stderr, io_lock, f"{vehicle_id} failed to send HELLO: {error}")
        return 1

    return 0


def send_messages(
    args: argparse.Namespace,
    *,
    client_factory: Callable[[str, int, float], TcpHelloClient] = TcpHelloClient,
    timestamp_factory: Callable[[], str] = iso_timestamp,
    sleeper: Callable[[float], None] = time.sleep,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    vehicle_ids = resolve_vehicle_ids(args)
    stop_event = threading.Event()
    io_lock = threading.Lock()

    if len(vehicle_ids) == 1:
        return send_vehicle_messages(
            args,
            vehicle_ids[0],
            client_factory=client_factory,
            timestamp_factory=timestamp_factory,
            sleeper=sleeper,
            stdout=stdout,
            stderr=stderr,
            io_lock=io_lock,
            stop_event=stop_event,
        )

    results = [0] * len(vehicle_ids)
    threads = []
    start_barrier = threading.Barrier(len(vehicle_ids))

    def worker(index: int, vehicle_id: str) -> None:
        results[index] = send_vehicle_messages(
            args,
            vehicle_id,
            client_factory=client_factory,
            timestamp_factory=timestamp_factory,
            sleeper=sleeper,
            stdout=stdout,
            stderr=stderr,
            io_lock=io_lock,
            stop_event=stop_event,
            start_barrier=start_barrier,
        )

    for index, vehicle_id in enumerate(vehicle_ids):
        thread = threading.Thread(target=worker, args=(index, vehicle_id), daemon=True)
        thread.start()
        threads.append(thread)

    try:
        for thread in threads:
            while thread.is_alive():
                thread.join(timeout=0.1)
    except KeyboardInterrupt:
        stop_event.set()
        write_line(stderr, io_lock, "stopped by user")
        for thread in threads:
            thread.join()
        return 130

    if any(result == 130 for result in results):
        return 130

    if any(result != 0 for result in results):
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return send_messages(args)


if __name__ == "__main__":
    raise SystemExit(main())
