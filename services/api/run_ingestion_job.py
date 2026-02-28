from __future__ import annotations

import argparse
import asyncio

from database import AsyncSessionFactory, init_db_schema
from event_ingestion import run_event_ingestion, run_scheduled_event_ingestion


async def _run(source_ids: list[str], reason: str) -> None:
    await init_db_schema()
    async with AsyncSessionFactory() as session:
        if source_ids:
            summary = await run_event_ingestion(
                session,
                source_ids=source_ids,
                reason=reason,
            )
        else:
            summary = await run_scheduled_event_ingestion(
                session,
                reason=reason,
            )

    print(summary.model_dump_json())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AFF event ingestion job")
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Optional source id. Provide multiple times to scope ingestion.",
    )
    parser.add_argument(
        "--reason",
        default="scheduled_sync",
        help="Execution reason stored in ingestion jobs/logs.",
    )
    args = parser.parse_args()

    asyncio.run(_run(source_ids=[str(item) for item in args.source_id], reason=args.reason))


if __name__ == "__main__":
    main()
