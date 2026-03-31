"""Allow `python -m tao_harness` to open the local CLI."""

from tao_harness.cli import _main


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
