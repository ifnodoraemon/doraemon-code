"""CLI entry point for the computer-use agent demo."""

from __future__ import annotations

import argparse
import asyncio
import socket
import threading
import time
from pathlib import Path

import httpx

from .crm_app import app
from .runner import ComputerUseRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Computer-use agent CRM demo")
    subcommands = parser.add_subparsers(dest="command", required=True)

    serve = subcommands.add_parser("serve", help="Start the local CRM demo app")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    run = subcommands.add_parser("run", help="Run the computer-use agent")
    run.add_argument("--goal", required=True)
    run.add_argument("--start-url", default=None)
    run.add_argument("--planner", choices=["scripted", "llm"], default="scripted")
    run.add_argument("--month", default="2026-05")
    run.add_argument("--trace-dir", type=Path, default=Path("/tmp/computer-use-agent-traces"))
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8765)
    run.add_argument("--no-start-server", action="store_true")
    run.add_argument("--headed", action="store_true")
    run.add_argument("--record-video", action="store_true")
    run.add_argument("--max-steps", type=int, default=20)

    args = parser.parse_args()
    if args.command == "serve":
        _serve(args.host, args.port)
        return

    if not args.no_start_server:
        _start_server_thread(args.host, args.port)
    start_url = args.start_url or f"http://{args.host}:{args.port}/"
    result = asyncio.run(
        ComputerUseRunner(
            goal=args.goal,
            start_url=start_url,
            planner_mode=args.planner,
            trace_dir=args.trace_dir,
            headless=not args.headed,
            max_steps=args.max_steps,
            month=args.month,
            record_video=args.record_video,
        ).run()
    )
    print(f"run_id={result.run_id}")
    print(f"success={result.success}")
    print(f"summary={result.summary}")
    print(f"trace_dir={result.trace_dir}")
    print(f"report={result.report_path}")
    if result.video_path:
        print(f"video={result.video_path}")
    for download in result.downloads:
        print(f"download={download}")


def _serve(host: str, port: int) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


def _start_server_thread(host: str, port: int) -> None:
    if _port_is_open(host, port):
        if _crm_ready(host, port):
            return
        raise RuntimeError(
            f"Port {host}:{port} is already in use by a different service. "
            "Use --port or --no-start-server with an explicit --start-url."
        )
    thread = threading.Thread(target=_serve, args=(host, port), daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if _crm_ready(host, port):
            return
        time.sleep(0.1)
    raise RuntimeError(f"Demo CRM did not start at http://{host}:{port}/")


def _crm_ready(host: str, port: int) -> bool:
    try:
        response = httpx.get(f"http://{host}:{port}/api/health", timeout=0.5)
        return response.json() == {"app": "computer-use-agent-crm-demo"}
    except (httpx.HTTPError, ValueError):
        return False


def _port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


if __name__ == "__main__":
    main()
