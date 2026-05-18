"""Controlled Playwright tools for the computer-use agent demo."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .models import BrowserAction, ToolResult
from .trace import TraceWriter


class BrowserSession:
    """Small whitelist wrapper around Playwright page operations."""

    def __init__(
        self,
        trace: TraceWriter,
        *,
        headless: bool = True,
        timeout_ms: int = 8000,
        record_video: bool = False,
        allowed_origin: str | None = None,
    ):
        self.trace = trace
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.record_video = record_video
        self.allowed_origin = allowed_origin.rstrip("/") if allowed_origin else None
        self.video_path: Path | None = None
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def start(self) -> None:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is required. Install with: pip install -e '.[browser]' "
                "&& playwright install chromium"
            ) from exc

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        context_options: dict[str, Any] = {"accept_downloads": True}
        if self.record_video:
            context_options["record_video_dir"] = str(self.trace.video_dir)
            context_options["record_video_size"] = {"width": 1280, "height": 720}
            context_options["viewport"] = {"width": 1280, "height": 720}
        self._context = await self._browser.new_context(**context_options)
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.timeout_ms)

    async def close(self) -> None:
        video = self._page.video if self._page and self.record_video else None
        if self._context:
            await self._context.close()
        if video:
            raw_path = Path(await video.path())
            target = self.trace.video_dir / "computer-use-demo.webm"
            if raw_path != target:
                shutil.copyfile(raw_path, target)
            self.video_path = target
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def execute(self, step_id: int, action: BrowserAction) -> ToolResult:
        if not self._page:
            return ToolResult(ok=False, observation="Browser is not started", error="not_started")

        try:
            if action.tool == "browser_open":
                result = await self._open(action.args)
            elif action.tool == "browser_snapshot":
                result = await self._snapshot()
            elif action.tool == "browser_click":
                result = await self._click(action.args)
            elif action.tool == "browser_fill":
                result = await self._fill(action.args)
            elif action.tool == "browser_extract":
                result = await self._extract(action.args)
            elif action.tool == "browser_download":
                result = await self._download(action.args)
            else:
                result = ToolResult(
                    ok=False,
                    observation=f"Tool is not allowed: {action.tool}",
                    error="tool_not_allowed",
                )
            if result.ok and self._page and not self._is_allowed_url(self._page.url):
                result = ToolResult(
                    ok=False,
                    observation=f"Page navigated outside the allowed demo origin: {self._page.url}",
                    error="url_not_allowed",
                    payload={"url": self._page.url},
                )
        except Exception as exc:  # Playwright raises provider-specific timeout/action errors.
            result = ToolResult(ok=False, observation=str(exc), error=exc.__class__.__name__)

        screenshot_path = await self._try_screenshot(step_id)
        if screenshot_path:
            result.screenshot_path = str(screenshot_path)
        return result

    async def _open(self, args: dict[str, Any]) -> ToolResult:
        url = str(args.get("url") or "")
        if not url:
            return ToolResult(ok=False, observation="Missing url", error="missing_url")
        if not self._is_allowed_url(url):
            return ToolResult(
                ok=False,
                observation=f"URL is outside the allowed demo origin: {url}",
                error="url_not_allowed",
            )
        await self._page.goto(url, wait_until="networkidle")
        return ToolResult(ok=True, observation=f"Opened {url}", payload={"url": self._page.url})

    def _is_allowed_url(self, url: str) -> bool:
        if not self.allowed_origin:
            return True
        target = urlparse(url)
        allowed = urlparse(self.allowed_origin)
        target_port = target.port or self._default_port(target.scheme)
        allowed_port = allowed.port or self._default_port(allowed.scheme)
        return target.scheme in {"http", "https"} and (
            target.scheme,
            target.hostname,
            target_port,
        ) == (
            allowed.scheme,
            allowed.hostname,
            allowed_port,
        )

    @staticmethod
    def _default_port(scheme: str) -> int | None:
        if scheme == "http":
            return 80
        if scheme == "https":
            return 443
        return None

    async def _snapshot(self) -> ToolResult:
        payload = await self._page.evaluate(
            """
            () => {
              const elements = Array.from(document.querySelectorAll(
                'button,input,textarea,a,[data-testid]'
              )).slice(0, 80).map((el) => ({
                tag: el.tagName.toLowerCase(),
                text: (el.innerText || el.value || el.getAttribute('aria-label') || '').trim(),
                testid: el.getAttribute('data-testid'),
                placeholder: el.getAttribute('placeholder'),
                href: el.getAttribute('href')
              }));
              return {
                title: document.title,
                url: location.href,
                text: document.body.innerText.slice(0, 4000),
                elements
              };
            }
            """
        )
        return ToolResult(ok=True, observation="Captured page snapshot", payload=payload)

    async def _click(self, args: dict[str, Any]) -> ToolResult:
        locator = self._locator(args)
        await locator.click()
        label = args.get("selector") or args.get("text") or args.get("testid")
        return ToolResult(ok=True, observation=f"Clicked {label}")

    async def _fill(self, args: dict[str, Any]) -> ToolResult:
        value = str(args.get("value", ""))
        locator = self._locator(args)
        await locator.fill(value)
        label = args.get("selector") or args.get("label") or args.get("placeholder") or args.get("testid")
        return ToolResult(ok=True, observation=f"Filled {label}", payload={"value": value})

    async def _extract(self, args: dict[str, Any]) -> ToolResult:
        query = str(args.get("query") or "visible_text")
        if query == "pending_customer_ids":
            customers = await self._page.evaluate(
                """
                () => Array.from(document.querySelectorAll('[data-customer-id]')).map((row) => ({
                  id: row.getAttribute('data-customer-id'),
                  name: row.querySelector('[data-field="name"]')?.innerText || '',
                  status: row.querySelector('[data-field="status"]')?.innerText || ''
                })).filter((row) => row.status === 'PENDING')
                """
            )
            ids = [item["id"] for item in customers]
            return ToolResult(
                ok=True,
                observation=f"Extracted {len(ids)} pending customer ids",
                payload={"customer_ids": ids, "customers": customers},
            )

        text = await self._page.locator("body").inner_text()
        pattern = args.get("regex")
        payload: dict[str, Any] = {"text": text[:4000]}
        if pattern:
            payload["matches"] = re.findall(str(pattern), text)
        return ToolResult(ok=True, observation="Extracted visible text", payload=payload)

    async def _download(self, args: dict[str, Any]) -> ToolResult:
        locator = self._locator(args)
        download_dir = self.trace.root / "downloads"
        download_dir.mkdir(exist_ok=True)
        async with self._page.expect_download() as download_info:
            await locator.click()
        download = await download_info.value
        suggested = download.suggested_filename or "download.bin"
        target = download_dir / suggested
        await download.save_as(target)
        return ToolResult(
            ok=True,
            observation=f"Downloaded {suggested}",
            payload={"filename": suggested},
            download_path=str(target),
        )

    def _locator(self, args: dict[str, Any]):
        if args.get("selector"):
            return self._page.locator(str(args["selector"])).first
        if args.get("testid"):
            return self._page.get_by_test_id(str(args["testid"])).first
        if args.get("label"):
            return self._page.get_by_label(str(args["label"])).first
        if args.get("placeholder"):
            return self._page.get_by_placeholder(str(args["placeholder"])).first
        if args.get("text"):
            return self._page.get_by_text(str(args["text"]), exact=bool(args.get("exact", False))).first
        raise ValueError("Action args must include selector, testid, label, placeholder, or text")

    async def _try_screenshot(self, step_id: int) -> Path | None:
        if not self._page:
            return None
        path = self.trace.screenshot_path(step_id)
        try:
            await self._page.screenshot(path=str(path), full_page=True)
            return path
        except Exception:
            return None
