# API Reference

## Core Classes

### HIDInterceptor

The main orchestrator for HID event monitoring.

#### Constructor

```python
class HIDInterceptor:
    def __init__(
        self,
        hooks: list[HookFn] | None = None,
        dispatcher: EventDispatcher | None = None,
        device_class: type[Device] = EvdevDevice,
    ) -> None:
        """Initialize the HIDInterceptor.

        Args:
            hooks: Optional list of hook functions to process events.
            dispatcher: Optional event dispatcher (for testing).
            device_class: Optional device class (for testing).
        """
```

**Parameters:**

- `hooks` (list[HookFn], optional): List of hook functions that will be called for each event
- `dispatcher` (EventDispatcher, optional): Custom event dispatcher (mainly for testing)
- `device_class` (type[Device], optional): Custom device class to use (mainly for testing)

**Example:**

```python
def my_hook(event: InputEvent) -> None:
    print(f"Event: {event}")

interceptor = HIDInterceptor(hooks=[my_hook])
```

#### Methods

##### `async run(stop_event: asyncio.Event) -> None`

Run the HID interception loop until the stop event is set.

**Parameters:**

- `stop_event` (asyncio.Event): An asyncio Event that signals when to stop monitoring

**Raises:**

- `asyncio.CancelledError`: If the task is cancelled during execution (handled gracefully with cleanup)

**Example:**

```python
import asyncio

async def main():
    interceptor = HIDInterceptor(hooks=[my_hook])
    stop_event = asyncio.Event()

    run_task = asyncio.create_task(interceptor.run(stop_event))

    try:
        await run_task
    except KeyboardInterrupt:
        stop_event.set()

asyncio.run(main())
```

## Event Types

All input events inherit from `InputEvent`.

### InputEvent (Union Type)

A discriminated union representing any input event.

**Possible Values:**
- `KeyEvent` - Keyboard or button events
- `RelEvent` - Relative movement events (mouse, scroll)
- `AbsEvent` - Absolute position events (touchpad, joystick)

**Common Properties:**

```python
class BaseEvent:
    device: str          # Device path (e.g., "/dev/input/event0")
    timestamp: float     # Event time (seconds since epoch)
    code: int           # Raw event code
    code_name: str      # Human-readable code name (e.g., "KEY_A")
    kind: InputKind     # Event type (KEY, REL, or ABS)
    value: int          # Event value (meaning depends on type)
```

### KeyEvent

Keyboard or button press events.

**Inherits:** `BaseEvent`

**Fields:**

- `value` (int): Key state
  - `0` = Key released (UP)
  - `1` = Key pressed (DOWN)
  - `2` = Key held (REPEAT)

**Example:**

```python
from hid_interceptor import KeyEvent, InputEvent

def handle_key(event: InputEvent) -> None:
    if isinstance(event, KeyEvent):
        states = {0: "UP", 1: "DOWN", 2: "REPEAT"}
        state = states.get(event.value, "UNKNOWN")
        print(f"Key {event.code_name}: {state}")
```

### RelEvent

Relative movement events (mouse movement, scroll wheel, trackball).

**Inherits:** `BaseEvent`

**Fields:**

- `value` (int): Relative movement amount

**Example:**

```python
from hid_interceptor import RelEvent, InputEvent

def handle_movement(event: InputEvent) -> None:
    if isinstance(event, RelEvent):
        axis_map = {
            "REL_X": "horizontal",
            "REL_Y": "vertical",
            "REL_WHEEL": "scroll"
        }
        axis = axis_map.get(event.code_name, "unknown")
        print(f"{axis} movement: {event.value}")
```

### AbsEvent

Absolute position events (touchpad coordinates, joystick axes, pressure).

**Inherits:** `BaseEvent`

**Fields:**

- `value` (int): Absolute position or value

**Example:**

```python
from hid_interceptor import AbsEvent, InputEvent

def handle_absolute(event: InputEvent) -> None:
    if isinstance(event, AbsEvent):
        print(f"Position {event.code_name}: {event.value}")
```

### InputKind

Enumeration of event types.

```python
class InputKind(Enum):
    KEY = "KEY"  # Keyboard or button (EV_KEY)
    REL = "REL"  # Relative movement (EV_REL)
    ABS = "ABS"  # Absolute position (EV_ABS)
```

## Hook Functions

A hook is a callable that processes events. Hooks are called synchronously for each event.

### Signature

```python
HookFn = Callable[[InputEvent], Any]
```

### Synchronous Hook

```python
def my_sync_hook(event: InputEvent) -> None:
    """Process an event synchronously."""
    if isinstance(event, KeyEvent):
        print(f"Key: {event.code_name}")
```

### Error Handling in Hooks

Hooks should handle their own exceptions. If a hook raises an exception:
- The exception is logged
- Other hooks continue to execute
- Event processing continues

```python
def safe_hook(event: InputEvent) -> None:
    """A hook with error handling."""
    try:
        # Your processing logic
        if isinstance(event, KeyEvent):
            print(f"Key: {event.code_name}")
    except Exception as e:
        print(f"Error processing event: {e}")
```

## Event Dispatcher

### EventDispatcher

Responsible for calling hooks for each event.

**Constructor:**

```python
class EventDispatcher:
    def __init__(self, hooks: list[HookFn] | None = None) -> None:
        """Initialize the dispatcher with optional hooks."""
```

**Methods:**

```python
async def dispatch(self, event: InputEvent) -> None:
    """Dispatch an event to all registered hooks."""
```

Usually you don't need to interact with EventDispatcher directly - it's used internally by HIDInterceptor.

## Input Devices

### Device (Abstract)

Abstract base class for input devices.

```python
class Device:
    """Abstract interface for input devices."""

    @property
    def path(self) -> str:
        """Path to the device (e.g., "/dev/input/event0")."""

    async def events(self) -> AsyncIterator[InputEvent]:
        """Iterate over input events from this device."""

    def close(self) -> None:
        """Close the device and release resources."""
```

### EvdevDevice

Concrete implementation using the evdev library.

Usually instantiated internally by HIDInterceptor, but can be used standalone:

```python
from hid_interceptor import EvdevDevice

device = await EvdevDevice.open("/dev/input/event0")
try:
    async for event in device.events():
        print(event)
finally:
    device.close()
```

## Exceptions

### HIDInterceptorError

Base exception for all HID Interceptor errors.

```python
class HIDInterceptorError(Exception):
    """Base exception for HID Interceptor."""
```

### DeviceError

Error related to device operations.

```python
class DeviceError(HIDInterceptorError):
    """Error related to device operations."""
```

### DeviceOpenError

Error when opening a device.

```python
class DeviceOpenError(DeviceError):
    """Error when opening a device."""
```

**Example:**

```python
from hid_interceptor import HIDInterceptor, InputEvent
from hid_interceptor.exceptions import DeviceOpenError
import asyncio


def my_hook(event: InputEvent) -> None:
    print(event)


async def main():
    try:
        interceptor = HIDInterceptor(hooks=[my_hook])
        stop_event = asyncio.Event()
        await interceptor.run(stop_event)
    except DeviceOpenError as e:
        print(f"Failed to open device: {e}")
    except Exception as e:
        print(f"Error: {e}")


asyncio.run(main())
```

## Type Aliases

```python
# A hook function
HookFn = Callable[[InputEvent], Any]

# An input event (union type)
InputEvent = KeyEvent | RelEvent | AbsEvent
```

## Models Module

All event types and enums are exported from `hid_interceptor.models`:

```python
from hid_interceptor.models import (
    AbsEvent,
    BaseEvent,
    InputEvent,
    InputKind,
    KeyEvent,
    RelEvent,
)
```

## Main Module Exports

```python
from hid_interceptor import (
    AbsEvent,
    BaseEvent,
    Device,
    DeviceError,
    DeviceOpenError,
    EvdevDevice,
    HIDInterceptor,
    HIDInterceptorError,
    InputEvent,
    InputKind,
    KeyEvent,
    RelEvent,
)
```
