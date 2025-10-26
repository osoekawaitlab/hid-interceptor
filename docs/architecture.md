# Architecture

## Overview

HID Interceptor is designed with clean separation of concerns and testability in mind. The architecture follows SOLID principles, particularly the Single Responsibility Principle and Dependency Inversion Principle.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User Application                        │
│              (asyncio event loop management)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ uses
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   HIDInterceptor                             │
│  (Orchestrates device discovery and event monitoring)        │
├─────────────────────────────────────────────────────────────┤
│  - Discovers and opens input devices                         │
│  - Creates monitoring tasks for each device                  │
│  - Handles graceful shutdown with stop_event                │
│  - Manages device cleanup in finally block                   │
└──┬────────────────────────────────────┬─────────────────────┘
   │                                    │
   │ uses                               │ uses
   ▼                                    ▼
┌──────────────────────┐    ┌──────────────────────────┐
│   Device Interface   │    │   EventDispatcher        │
│  (Abstract)          │    │ (Routes events to hooks) │
├──────────────────────┤    ├──────────────────────────┤
│ - events(): Async    │    │ - dispatch(event)        │
│   generator          │    │ - Calls all hooks        │
│ - close()            │    └──────────────────────────┘
└──┬───────────────────┘           │
   │                               │
   │ implements                     │ uses
   ▼                               ▼
┌──────────────────────┐    ┌──────────────────────────┐
│   EvdevDevice        │    │    Hook Functions        │
│ (evdev wrapper)      │    │  (User callbacks)        │
├──────────────────────┤    └──────────────────────────┘
│ - Wraps evdev        │
│ - Converts to domain │
│   models             │
│ - Handles device     │
│   lifecycle          │
└──────────────────────┘
```

## Core Components

### HIDInterceptor

**Responsibility:** Orchestrate the entire HID event interception process

**Key Features:**
- Discovers input devices using `evdev.list_devices()`
- Opens devices via `Device.open()` (overridable for testing)
- Creates async tasks to monitor each device
- Implements graceful shutdown via `stop_event`
- Ensures proper resource cleanup in `finally` block

**Design Decisions:**
- User is responsible for managing the asyncio event loop (not embedded)
- Accepts `stop_event` parameter for clean shutdown control
- Provides dependency injection for `device_class` to enable testing
- Handles `asyncio.CancelledError` gracefully

### Device Interface

**Responsibility:** Abstract away device-specific implementation details

**Interface:**

```python
class Device(ABC):
    @property
    def path(self) -> str: ...

    async def events(self) -> AsyncIterator[InputEvent]: ...

    def close(self) -> None: ...
```

**Rationale:**
- Allows swapping different device backends (evdev, mock, etc.)
- Makes testing easier with mock devices
- Decouples application logic from low-level details

### EvdevDevice

**Responsibility:** Bridge between evdev library and domain models

**Key Features:**
- Wraps `evdev.InputDevice` for async event reading
- Converts raw evdev events to domain `InputEvent` objects
- Handles device grab/ungrab for exclusive access
- Implements proper cleanup in context managers

**Design Notes:**
- Uses `evdev.async_read_loop()` for async event reading
- Converts raw events to typed `RawInputEvent` dict format
- Delegates event conversion to `convert_raw_event()` function

### EventDispatcher

**Responsibility:** Route events to user-provided hooks

**Key Features:**
- Maintains list of hook functions
- Calls all hooks for each event synchronously
- Catches exceptions in hooks to prevent cascade failures
- Logs errors for debugging

**Design Notes:**
- Hooks are called sequentially (not concurrently)
- One hook failure doesn't affect others
- All hooks receive the same event

### Event Converter

**Responsibility:** Convert raw device events to domain models

**Key Features:**
- Converts raw events to typed `InputEvent` objects
- Resolves code names from evdev's ecodes tables
- Returns `None` for unsupported event types
- Pure function for testability

**Supported Event Types:**
- `EV_KEY` → `KeyEvent`
- `EV_REL` → `RelEvent`
- `EV_ABS` → `AbsEvent`

### Event Models

**Responsibility:** Provide type-safe event representation

**Hierarchy:**

```
BaseEvent (abstract)
├── KeyEvent (kind = InputKind.KEY)
├── RelEvent (kind = InputKind.REL)
└── AbsEvent (kind = InputKind.ABS)

Type Union:
InputEvent = KeyEvent | RelEvent | AbsEvent
```

**Benefits:**
- Type-safe event handling with pattern matching
- IDE support for event attributes
- mypy validation at development time

## Design Patterns

### Dependency Injection

Components accept dependencies as constructor parameters:

```python
# Production
interceptor = HIDInterceptor(hooks=[my_hook])

# Testing
interceptor = HIDInterceptor(
    dispatcher=mock_dispatcher,
    device_class=MockDevice
)
```

### Graceful Shutdown

Uses asyncio.Event for clean shutdown signaling:

```python
run_task = asyncio.create_task(interceptor.run(stop_event))
# ... monitor events ...
stop_event.set()  # Signal shutdown
await run_task    # Wait for cleanup
```

### Error Handling

Distinguishes between different error scenarios:

```python
try:
    await interceptor.run(stop_event)
except asyncio.CancelledError:
    # Task was cancelled - cleanup happens in finally
except KeyboardInterrupt:
    # User pressed Ctrl+C
finally:
    # Always cleanup devices
```

## Async Architecture

### Event Loop Management

- User creates and manages the main asyncio event loop
- HIDInterceptor provides `async def run()` method
- Each device gets its own monitoring task

### Task Management

```python
# Create tasks for device monitoring
tasks = [
    asyncio.create_task(self._monitor_one_device(device))
    for device in opened_devices
]

# Cancel all tasks on shutdown
for task in tasks:
    task.cancel()

# Wait for cancellation to complete
await asyncio.gather(*tasks, return_exceptions=True)
```

### CancelledError Handling

Gracefully handles task cancellation:

```python
try:
    await stop_event.wait()
except asyncio.CancelledError:
    logger.info("Monitoring task cancelled - initiating cleanup...")

# Cleanup continues regardless
for task in tasks:
    task.cancel()
```

## Type Safety

The project uses:

- **Python 3.10+ type hints** - Full type annotations
- **Union types** - `InputEvent = KeyEvent | RelEvent | AbsEvent`
- **Type guards** - `isinstance(event, KeyEvent)` for narrowing
- **Pattern matching** - `match event:` statements (Python 3.10+)
- **mypy** - Static type checking in CI/CD

## Testing Strategy

### Unit Testing

- Mock `Device` class for isolated component testing
- Mock `EventDispatcher` to verify event routing
- Test error paths and edge cases

### Integration Testing

- Use real device paths with mock devices
- Test full `run()` lifecycle
- Verify proper cleanup with `asyncio.CancelledError`

### Testability Features

- Constructor dependency injection
- Abstract `Device` interface
- Pure conversion functions
- No global state

## Exception Hierarchy

```
Exception (built-in)
└── HIDInterceptorError (domain base)
    ├── DeviceError (device-related)
    │   └── DeviceOpenError (opening failed)
    └── [Future: DispatchError, etc.]
```

## Performance Considerations

- **Event Reading:** Async generator for non-blocking I/O
- **Hook Execution:** Synchronous but fast (delegates to user)
- **Memory:** Minimal object creation per event
- **File Descriptors:** One per opened device

## Future Extensibility

The architecture supports:

- Alternative device backends (not just evdev)
- Custom event filters/preprocessing
- Async hook support (if needed)
- Hot device detection/removal
- Event buffering/queueing
