from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
from typing import Iterable

from ..models import OutboundMessage
from .config import LiveDiscordTestError, load_live_test_config
from .harness import LiveDiscordTestHarness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run live Discord framework verification flows.")
    parser.add_argument(
        "--dotenv",
        dest="dotenv",
        help="Optional path to a dotenv file containing DISCORD_TEST_* variables.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser(
        "verify",
        help="Send a message, confirm it appears in history, and clean up.",
    )
    _channel_options(verify)
    verify.add_argument(
        "--content",
        help="Override message content. Defaults to a timestamp payload.",
    )
    verify.add_argument(
        "--history-limit",
        type=int,
        default=20,
        help="Number of recent messages to inspect when verifying delivery (default: 20).",
    )
    verify.add_argument(
        "--keep",
        action="store_true",
        help="Do not delete the verification message after completion.",
    )

    send = subparsers.add_parser(
        "send-message",
        help="Send a message and optionally delete it afterward.",
    )
    _channel_options(send)
    send.add_argument("--content", help="Message content to send.")
    send.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the message after sending.",
    )

    dm = subparsers.add_parser(
        "send-dm",
        help="Send a direct message to a configured user alias.",
    )
    dm.add_argument(
        "--user-alias",
        help="Configured DM alias defined by DISCORD_TEST_DM_TARGETS.",
    )
    dm.add_argument("--user-id", help="Explicit user ID to DM.")
    dm.add_argument("--content", help="Message content to send.")
    dm.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the DM after sending (requires message permissions).",
    )

    return parser


def _channel_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--channel-alias",
        help="Configured channel alias defined by DISCORD_TEST_CHANNELS.",
    )
    parser.add_argument("--channel-id", help="Explicit channel ID to target.")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        config = load_live_test_config(dotenv_path=args.dotenv)
    except LiveDiscordTestError as exc:
        parser.error(str(exc))
        return 2

    async def runner() -> int:
        async with LiveDiscordTestHarness(config) as harness:
            if args.command == "verify":
                return await _command_verify(args, harness)
            if args.command == "send-message":
                return await _command_send_message(args, harness)
            if args.command == "send-dm":
                return await _command_send_dm(args, harness)
            raise LiveDiscordTestError(f"Unknown command: {args.command}")

    try:
        return asyncio.run(runner())
    except LiveDiscordTestError as exc:
        parser.error(str(exc))
        return 2


async def _command_verify(args, harness: LiveDiscordTestHarness) -> int:
    content = args.content or _timestamped_content("verify")
    result = await harness.send_message(
        OutboundMessage(content=content),
        channel_alias=args.channel_alias,
        channel_id=args.channel_id,
    )

    history = await harness.fetch_recent_messages(
        channel_alias=args.channel_alias,
        channel_id=args.channel_id,
        limit=args.history_limit,
    )
    if not any(msg.id == result.message.id for msg in history if msg.id):
        raise LiveDiscordTestError("Verification failed: message did not appear in recent history")

    if not args.keep:
        await harness.cleanup_messages([result])

    channel_ref = args.channel_id or args.channel_alias or harness.config.resolve_channel()
    print(f"Sent and verified message {result.message.id} in channel {channel_ref}")
    return 0


async def _command_send_message(args, harness: LiveDiscordTestHarness) -> int:
    content = args.content or _timestamped_content("send")
    result = await harness.send_message(
        OutboundMessage(content=content),
        channel_alias=args.channel_alias,
        channel_id=args.channel_id,
    )
    channel_ref = args.channel_id or args.channel_alias or harness.config.resolve_channel()
    print(f"Sent message {result.message.id} to channel {channel_ref}")
    if args.cleanup:
        await harness.cleanup_messages([result])
        print("Message cleaned up")
    return 0


async def _command_send_dm(args, harness: LiveDiscordTestHarness) -> int:
    if not args.user_alias and not args.user_id:
        raise LiveDiscordTestError("Provide --user-alias or --user-id for DM operations")

    content = args.content or _timestamped_content("dm")
    result = await harness.send_dm(
        OutboundMessage(content=content),
        user_alias=args.user_alias,
        user_id=args.user_id,
    )
    print(f"Sent DM {result.message.id} to user {args.user_alias or args.user_id}")
    if args.cleanup:
        await harness.cleanup_messages([result])
        print("DM cleaned up")
    return 0


def _timestamped_content(tag: str) -> str:
    return f"[discord-framework::{tag}] {datetime.utcnow().isoformat()}"


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    raise SystemExit(main())
