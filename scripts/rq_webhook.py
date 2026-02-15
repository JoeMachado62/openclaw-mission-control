#!/usr/bin/env python
"""RQ helpers for background queue processing."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_ROOT = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.webhooks.dispatch import flush_webhook_delivery_queue


def cmd_worker(args: argparse.Namespace) -> int:
    interval_seconds = max(args.interval_seconds, 0.0)
    try:
        while True:
            asyncio.run(
                flush_webhook_delivery_queue(
                    block=True,
                    block_timeout=interval_seconds,
                ),
            )
    except KeyboardInterrupt:
        return 0
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Background RQ helper commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    worker_parser = subparsers.add_parser("worker", help="Continuously process queued work.")
    worker_parser.add_argument(
        "--interval-seconds",
        type=float,
        default=float(os.environ.get("WEBHOOK_WORKER_INTERVAL_SECONDS", "2")),
        help="Seconds to wait for queue work before returning when idle.",
    )
    worker_parser.set_defaults(func=cmd_worker)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
