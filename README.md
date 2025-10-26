# hid-interceptor

A Python-based HID event interceptor for Linux that monitors `/dev/input/event*` devices and dispatches input events to user-defined hooks.

## Features

- **Intercepts HID events** from input devices (keyboards, mice, etc.)
- **Custom event hooks** - Define callback functions to process events
- **Multiple device support** - Monitor all input devices simultaneously
- **Type-safe** - Full type annotations for IDE support and static analysis
- **Graceful shutdown** - Properly handles interrupts and cleanup
- **Async-first** - Built on asyncio for efficient event handling
- **Lightweight** - Minimal dependencies, efficient event processing

## Installation

```bash
pip install https://github.com/osoekawaitlab/hid-interceptor
```

## Quick Start

```python
from hid_interceptor import InputEvent, HIDInterceptor
import asyncio


def my_hook(event: InputEvent) -> None:
    """Process input events."""
    print(f"Event: {event}", flush=True)


async def main():
    # Create an interceptor with your hook
    interceptor = HIDInterceptor(hooks=[my_hook])
    stop_event = asyncio.Event()

    # Run the interceptor in a background task
    run_task = asyncio.create_task(interceptor.run(stop_event))

    # Handle keyboard interrupt
    try:
        await run_task
    except KeyboardInterrupt:
        print("Stopping...", flush=True)
        stop_event.set()


if __name__ == "__main__":
    asyncio.run(main())
```

## Architecture

The library is organized around these key components:

- **HIDInterceptor**: Main orchestrator that manages the event loop lifecycle and device coordination
- **Device**: Abstract interface for input devices
- **EvdevDevice**: Concrete implementation wrapping the evdev library
- **EventDispatcher**: Routes events to registered hooks
- **Models**: Type-safe event models (KeyEvent, RelEvent, AbsEvent)

## Usage

### Basic Usage with Hooks

```python
from hid_interceptor import InputEvent, HIDInterceptor, KeyEvent
import asyncio


def keyboard_hook(event: InputEvent) -> None:
    """Handle keyboard events."""
    if isinstance(event, KeyEvent):
        print(f"Key pressed: {event.code_name} (value: {event.value})")


def mouse_hook(event: InputEvent) -> None:
    """Handle mouse events."""
    print(f"Mouse event from {event.device}: {event}")


async def main():
    interceptor = HIDInterceptor(hooks=[keyboard_hook, mouse_hook])
    stop_event = asyncio.Event()

    # Run until interrupted
    try:
        await interceptor.run(stop_event)
    except KeyboardInterrupt:
        stop_event.set()


asyncio.run(main())
```

### Advanced: Custom Event Processing

```python
from hid_interceptor import InputEvent, HIDInterceptor, KeyEvent, RelEvent
import asyncio


def advanced_hook(event: InputEvent) -> None:
    """Process different event types differently."""
    match event:
        case KeyEvent():
            print(f"Key: {event.code_name} on device {event.device}")
        case RelEvent():
            print(f"Relative motion: axis={event.code_name}, value={event.value}")
        case _:
            print(f"Other event: {event.kind}")


async def main():
    interceptor = HIDInterceptor(hooks=[advanced_hook])
    stop_event = asyncio.Event()
    await interceptor.run(stop_event)


asyncio.run(main())
```

## Important Notes

⚠️ **Keyboard/Input Capture**: This library captures ALL events from monitored input devices. This includes:
- Keyboard input
- Mouse movements and clicks
- Other input device events

⚠️ **SIGINT Handling**: On some systems, capturing all keyboard events may interfere with sending Ctrl+C to the process. If this happens:
1. Use SSH or a remote terminal to run the script
2. Use a separate terminal to send signals (e.g., `kill -SIGTERM <pid>`)
3. The library handles graceful shutdown via `stop_event.set()`

## API Reference

### HIDInterceptor

```python
class HIDInterceptor:
    def __init__(
        self,
        hooks: list[HookFn] | None = None,
        dispatcher: EventDispatcher | None = None,
        device_class: type[Device] = EvdevDevice,
    ) -> None:
        """Initialize the HID interceptor."""

    async def run(self, stop_event: asyncio.Event) -> None:
        """Run the HID interception loop.

        Args:
            stop_event: An asyncio Event that signals when to stop monitoring.
        """
```

### Event Types

All events inherit from `InputEvent` and include:
- **device** (str): Path to the device (e.g., `/dev/input/event0`)
- **timestamp** (float): Event timestamp
- **code** (int): Event code
- **code_name** (str): Human-readable code name
- **value** (int): Event value
- **kind** (InputKind): Type of event (KEY, REL, ABS)

#### KeyEvent
Keyboard and button events

#### RelEvent
Relative motion events (mouse movement, scroll wheels)

#### AbsEvent
Absolute position events (touchpads, joysticks)

## Requirements

- Python 3.10+
- Linux with evdev support
- Root or appropriate permissions to read `/dev/input/event*` files

## License

MIT License. See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure all tests pass and maintain type safety with mypy.
