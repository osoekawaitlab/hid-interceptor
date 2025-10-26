"""Domain-level exceptions for HID Interceptor.

This module defines the exception hierarchy for the HID Interceptor library.
All exceptions inherit from HIDInterceptorError, with more specific exceptions
for different failure scenarios.

Exception Hierarchy:
    HIDInterceptorError (base)
    └── DeviceError
        └── DeviceOpenError
"""


class HIDInterceptorError(Exception):
    """Base exception for HID Interceptor domain errors."""


class DeviceError(HIDInterceptorError):
    """Base exception for device-related errors."""


class DeviceOpenError(DeviceError):
    """Raised when a device cannot be opened or grabbed."""
