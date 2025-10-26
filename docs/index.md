# HID Interceptor

A Python-based HID event interceptor for Linux that monitors input devices and dispatches events to user-defined hooks.

## Features

- **Monitor Input Devices** - Intercepts events from keyboards, mice, and other input devices
- **Custom Event Hooks** - Define callback functions to process events in real-time
- **Type-Safe** - Full type annotations for IDE support and static analysis with mypy
- **Graceful Shutdown** - Properly handles interrupts and resource cleanup
- **Async-First** - Built on asyncio for efficient, non-blocking event handling
- **Multiple Devices** - Monitor all input devices simultaneously
- **Lightweight** - Minimal dependencies, efficient event processing

## Quick Example

```python
from hid_interceptor import InputEvent, HIDInterceptor, KeyEvent
import asyncio


def my_hook(event: InputEvent) -> None:
    """Process input events."""
    if isinstance(event, KeyEvent):
        print(f"Key: {event.code_name} (value: {event.value})")


async def main():
    interceptor = HIDInterceptor(hooks=[my_hook])
    stop_event = asyncio.Event()

    run_task = asyncio.create_task(interceptor.run(stop_event))

    try:
        await run_task
    except KeyboardInterrupt:
        print("Stopping...")
        stop_event.set()


if __name__ == "__main__":
    asyncio.run(main())
```

## Installation

```bash
pip install https://github.com/osoekawaitlab/hid-interceptor
```

## Next Steps

- [Getting Started](getting-started.md) - Learn how to use the library
- [API Reference](api.md) - Detailed API documentation
- [Architecture](architecture.md) - Understanding the design

## Requirements

- Python 3.10+
- Linux with evdev support
- Root or appropriate permissions to read `/dev/input/event*` files

## License

MIT License. See LICENSE file for details.
