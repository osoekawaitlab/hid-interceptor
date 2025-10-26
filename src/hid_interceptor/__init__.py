"""HID Interceptor python library.

A library for monitoring and intercepting HID (Human Interface Device) events on Linux.
"""

from hid_interceptor.device import Device
from hid_interceptor.evdev_device import EvdevDevice
from hid_interceptor.exceptions import (
    DeviceError,
    DeviceOpenError,
    HIDInterceptorError,
)
from hid_interceptor.interceptor import HIDInterceptor
from hid_interceptor.models import (
    AbsEvent,
    BaseEvent,
    InputEvent,
    InputKind,
    KeyEvent,
    RelEvent,
)

__version__ = "0.1.0"

__all__ = [
    "AbsEvent",
    "BaseEvent",
    "Device",
    "DeviceError",
    "DeviceOpenError",
    "EvdevDevice",
    "HIDInterceptor",
    "HIDInterceptorError",
    "InputEvent",
    "InputKind",
    "KeyEvent",
    "RelEvent",
    "__version__",
]
