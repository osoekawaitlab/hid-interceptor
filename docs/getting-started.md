# Getting Started

## Installation

Install hid-interceptor from GitHub:

```bash
pip install https://github.com/osoekawaitlab/hid-interceptor
```

## Basic Usage

### Minimal Example

The simplest way to start monitoring input events:

```python
from hid_interceptor import InputEvent, HIDInterceptor
import asyncio


def print_event(event: InputEvent) -> None:
    """Print every input event."""
    print(event)


async def main():
    interceptor = HIDInterceptor(hooks=[print_event])
    stop_event = asyncio.Event()

    run_task = asyncio.create_task(interceptor.run(stop_event))

    try:
        await run_task
    except KeyboardInterrupt:
        stop_event.set()


asyncio.run(main())
```

### Working with Specific Event Types

Process only keyboard events:

```python
from hid_interceptor import InputEvent, HIDInterceptor, KeyEvent
import asyncio


def keyboard_handler(event: InputEvent) -> None:
    """Handle only keyboard events."""
    if isinstance(event, KeyEvent):
        state = {0: "UP", 1: "DOWN", 2: "REPEAT"}.get(event.value, "UNKNOWN")
        print(f"Key {event.code_name}: {state}")


async def main():
    interceptor = HIDInterceptor(hooks=[keyboard_handler])
    stop_event = asyncio.Event()

    run_task = asyncio.create_task(interceptor.run(stop_event))

    try:
        await run_task
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_event.set()


asyncio.run(main())
```

### Multiple Hooks

Register multiple handlers for different purposes:

```python
from hid_interceptor import InputEvent, HIDInterceptor, KeyEvent, RelEvent
import asyncio


def log_all(event: InputEvent) -> None:
    """Log all events."""
    print(f"[{event.device}] {event.code_name}: {event.value}")


def filter_keys(event: InputEvent) -> None:
    """Process only keyboard events separately."""
    if isinstance(event, KeyEvent):
        # Custom processing for keys
        pass


def filter_mouse(event: InputEvent) -> None:
    """Process only mouse events."""
    if isinstance(event, RelEvent):
        # Custom processing for mouse
        pass


async def main():
    # All three hooks will be called for each event
    interceptor = HIDInterceptor(
        hooks=[log_all, filter_keys, filter_mouse]
    )
    stop_event = asyncio.Event()

    run_task = asyncio.create_task(interceptor.run(stop_event))

    try:
        await run_task
    except KeyboardInterrupt:
        stop_event.set()


asyncio.run(main())
```

## Running with Permissions

Since HID event access requires special permissions, you may need to:

### Option 1: Run as Root

```bash
sudo python your_script.py
```

### Option 2: Add Your User to the Input Group

```bash
sudo usermod -a -G input $USER
# Log out and back in
```

Then verify your devices:

```bash
ls -l /dev/input/event*
```

## Handling Keyboard Interrupts

The library properly handles Ctrl+C and gracefully shuts down:

```python
import asyncio
from hid_interceptor import InputEvent, HIDInterceptor


def my_hook(event: InputEvent) -> None:
    print(event)


async def main():
    interceptor = HIDInterceptor(hooks=[my_hook])
    stop_event = asyncio.Event()

    run_task = asyncio.create_task(interceptor.run(stop_event))

    try:
        await run_task
    except KeyboardInterrupt:
        print("\nGracefully shutting down...")
        stop_event.set()
        # Devices are automatically closed in the finally block


asyncio.run(main())
```

## Common Patterns

### Event Rate Limiting

```python
from hid_interceptor import InputEvent, HIDInterceptor
import asyncio
import time


class RateLimiter:
    def __init__(self, min_interval: float = 0.1):
        self.min_interval = min_interval
        self.last_event_time = 0

    def should_process(self) -> bool:
        now = time.time()
        if now - self.last_event_time >= self.min_interval:
            self.last_event_time = now
            return True
        return False


limiter = RateLimiter(min_interval=0.1)


def rate_limited_hook(event: InputEvent) -> None:
    if limiter.should_process():
        print(f"Event: {event.code_name}")


async def main():
    interceptor = HIDInterceptor(hooks=[rate_limited_hook])
    stop_event = asyncio.Event()

    run_task = asyncio.create_task(interceptor.run(stop_event))

    try:
        await run_task
    except KeyboardInterrupt:
        stop_event.set()


asyncio.run(main())
```

### Event Filtering

```python
from hid_interceptor import InputEvent, HIDInterceptor, KeyEvent, InputKind
import asyncio


def only_letter_keys(event: InputEvent) -> None:
    """Only process letter keys (A-Z)."""
    if isinstance(event, KeyEvent):
        # Simple filter for common letter key codes
        letter_keys = {
            "KEY_A", "KEY_B", "KEY_C", "KEY_D", "KEY_E", "KEY_F", "KEY_G",
            "KEY_H", "KEY_I", "KEY_J", "KEY_K", "KEY_L", "KEY_M", "KEY_N",
            # ... etc
        }
        if event.code_name in letter_keys and event.value == 1:  # Key down
            print(f"Letter pressed: {event.code_name}")


async def main():
    interceptor = HIDInterceptor(hooks=[only_letter_keys])
    stop_event = asyncio.Event()

    run_task = asyncio.create_task(interceptor.run(stop_event))

    try:
        await run_task
    except KeyboardInterrupt:
        stop_event.set()


asyncio.run(main())
```

## Testing Your Setup

Verify that the library can detect your devices:

```python
from evdev import list_devices
import sys


print("Available input devices:")
devices = list_devices()
if not devices:
    print("No devices found. Check permissions.")
    sys.exit(1)

for device_path in devices:
    print(f"  {device_path}")
```

## Next Steps

- Learn about all available [event types](api.md#event-types)
- Read the [Architecture](architecture.md) to understand design decisions
- Check the [API Reference](api.md) for detailed documentation
