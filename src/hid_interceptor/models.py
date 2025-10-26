"""Data models for HID events."""

from enum import Enum
from typing import Annotated, Literal

from evdev import ecodes
from pydantic import BaseModel, ConfigDict, Field

from hid_interceptor.device import RawInputEvent


class InputKind(str, Enum):
    """Enumeration of HID input event types."""

    KEY = "KEY"  # EV_KEY - Keyboard or button events
    REL = "REL"  # EV_REL - Relative movement events (mouse)
    ABS = "ABS"  # EV_ABS - Absolute position events (touchpad)


class BaseEvent(BaseModel):
    """Base class for all HID events.

    This class defines the common fields present in all input events.
    Events are immutable (frozen) to prevent accidental modifications.

    Attributes:
        kind: The type of input event (KEY, REL, or ABS)
        device: Path to the input device (e.g., /dev/input/event0)
        timestamp: Event timestamp in seconds since epoch (with microsecond precision)
        code: Raw event code from the kernel
        code_name: Human-readable name for the event code
    """

    model_config = ConfigDict(frozen=True)

    kind: InputKind
    device: str
    timestamp: float
    code: int
    code_name: str


class KeyEvent(BaseEvent):
    """Keyboard or button event.

    Represents key press/release or button events.

    Attributes:
        value: Key state (0=UP, 1=DOWN, 2=REPEAT)
        kind: Always InputKind.KEY for this event type
    """

    kind: Literal[InputKind.KEY] = InputKind.KEY
    value: int = Field(ge=0, le=2, description="Key state: 0=UP, 1=DOWN, 2=REPEAT")


class RelEvent(BaseEvent):
    """Relative movement event.

    Represents relative motion like mouse movement or scroll wheel changes.

    Attributes:
        value: Relative value (movement delta or scroll amount)
        kind: Always InputKind.REL for this event type
    """

    kind: Literal[InputKind.REL] = InputKind.REL
    value: int = Field(description="Relative value (can be negative)")


class AbsEvent(BaseEvent):
    """Absolute position event.

    Represents absolute coordinates like touchpad position.

    Attributes:
        value: Absolute value (coordinate or position)
        kind: Always InputKind.ABS for this event type
    """

    kind: Literal[InputKind.ABS] = InputKind.ABS
    value: int = Field(description="Absolute value (position coordinate)")


# Discriminated Union type using Pydantic's Field(discriminator=...)
# This allows automatic deserialization of the correct event type based on 'kind'
InputEvent = Annotated[KeyEvent | RelEvent | AbsEvent, Field(discriminator="kind")]


def convert_raw_event(raw_event: RawInputEvent, device_path: str) -> InputEvent | None:
    """Convert a raw input event to a domain InputEvent.

    Args:
        raw_event: The raw event from the device
        device_path: The device path where the event originated

    Returns:
        An InputEvent object, or None if the event type is not supported
    """
    ts = raw_event["sec"] + raw_event["usec"] / 1e6

    if raw_event["type"] == ecodes.EV_KEY:
        # Look up key name from ecodes
        key_name = ecodes.BTN.get(
            raw_event["code"],
            ecodes.KEY.get(raw_event["code"], None),
        )

        return KeyEvent(
            kind=InputKind.KEY,
            device=device_path,
            timestamp=ts,
            code=raw_event["code"],
            code_name=str(key_name or raw_event["code"]),
            value=raw_event["value"],
        )

    if raw_event["type"] == ecodes.EV_REL:
        return RelEvent(
            kind=InputKind.REL,
            device=device_path,
            timestamp=ts,
            code=raw_event["code"],
            code_name=str(ecodes.REL.get(raw_event["code"], raw_event["code"])),
            value=raw_event["value"],
        )

    if raw_event["type"] == ecodes.EV_ABS:
        return AbsEvent(
            kind=InputKind.ABS,
            device=device_path,
            timestamp=ts,
            code=raw_event["code"],
            code_name=str(ecodes.ABS.get(raw_event["code"], raw_event["code"])),
            value=raw_event["value"],
        )

    return None
