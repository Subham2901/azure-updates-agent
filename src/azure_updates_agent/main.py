"""Single entrypoint: fetch, reconcile, render, write."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from azure_updates_agent.mcp_client import (
    build_product_filter,
    enrich_with_full_descriptions,
    fetch_product_taxonomy,
    fetch_updates,
)
from azure_updates_agent.report import render_report
from azure_updates_agent.state import StateStore
from azure_updates_agent.watchlist import (
    WatchlistValidationError,
    load_watchlist,
    verify_against_taxonomy,
)

logger = logging.getLogger(__name__)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Track Azure updates for watched services.")
    p.add_argument("--config", type=Path, default=Path("config/watchlist.yaml"))
    p.add_argument("--state", type=Path, default=Path("state.db"))
    p.add_argument("--out", type=Path, default=Path("reports/latest.md"))
    p.add_argument("--days", type=int, default=7, help="lookback window in days")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="fetch and render but do NOT touch state or write files",
    )
    return p.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    watchlist = load_watchlist(args.config)

    taxonomy = await fetch_product_taxonomy()
    try:
        verify_against_taxonomy(watchlist, taxonomy)
    except WatchlistValidationError as e:
        logger.error("watchlist validation failed:\n%s", e)
        return 2

    since = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    updates = await fetch_updates(build_product_filter(list(watchlist.products), since))
    logger.info("fetched %d updates since %s", len(updates), since)

    if args.dry_run:
        logger.info("dry run: skipping state reconcile and report write")
        return 0

    store = StateStore(args.state)
    try:
        delta = store.reconcile(updates)
    finally:
        store.close()

    if delta.new:
        new_enriched = await enrich_with_full_descriptions(list(delta.new))
        from azure_updates_agent.state import Delta
        delta = Delta(
            new=tuple(new_enriched),
            changed=delta.changed,
            unchanged_count=delta.unchanged_count,
        )

    md = render_report(delta, list(watchlist.products), since)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md)
    logger.info(
        "report written to %s (%d new, %d changed)",
        args.out, len(delta.new), len(delta.changed),
    )
    return 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    try:
        exit_code = asyncio.run(run(parse_args(sys.argv[1:])))
    except Exception as exc:  # noqa: BLE001 - top-level guard for clean CLI exit
        logger.error("run failed: %s", exc)
        logger.error("This is often a transient MRC server issue; try again shortly.")
        exit_code = 1
    sys.exit(exit_code)