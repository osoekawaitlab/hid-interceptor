"""Tests for data models in hid_interceptor.models."""

import pytest
from pydantic import TypeAdapter, ValidationError

from hid_interceptor.models import (
    AbsEvent,
    BaseEvent,
    InputEvent,
    InputKind,
    KeyEvent,
    RelEvent,
)

# Test constants
TEST_TIMESTAMP = 1234567890.123456
KEY_EVENT_VALUE_DOWN = 1
KEY_EVENT_VALUE_REPEAT = 2
REL_EVENT_VALUE = 5
REL_EVENT_NEGATIVE_VALUE = -10
ABS_EVENT_VALUE = 100
ABS_EVENT_MAX_VALUE = 65535


class TestInputKind:
    """Test InputKind enum."""

    def test_input_kind_has_required_values(self) -> None:
        """Test that InputKind has KEY, REL, and ABS values."""
        assert InputKind.KEY.value == "KEY"
        assert InputKind.REL.value == "REL"
        assert InputKind.ABS.value == "ABS"

    def test_input_kind_is_string_enum(self) -> None:
        """Test that InputKind is a string enum."""
        assert isinstance(InputKind.KEY, str)
        assert isinstance(InputKind.REL, str)
        assert isinstance(InputKind.ABS, str)


class TestBaseEvent:
    """Test BaseEvent model."""

    def test_base_event_creation(self) -> None:
        """Test creating a BaseEvent."""
        event = BaseEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.123456,
            code=1,
            code_name="KEY_A",
        )
        assert event.kind == InputKind.KEY
        assert event.device == "/dev/input/event0"
        assert event.timestamp == TEST_TIMESTAMP
        assert event.code == 1
        assert event.code_name == "KEY_A"

    def test_base_event_is_frozen(self) -> None:
        """Test that BaseEvent is immutable (frozen)."""
        event = BaseEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
        )
        with pytest.raises(ValidationError):
            event.kind = InputKind.REL

    def test_base_event_missing_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            BaseEvent(  # type: ignore[call-arg]
                kind=InputKind.KEY, device="/dev/input/event0", timestamp=1.0
            )


class TestKeyEvent:
    """Test KeyEvent model."""

    def test_key_event_creation(self) -> None:
        """Test creating a KeyEvent."""
        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,  # DOWN
        )
        assert event.kind == InputKind.KEY
        assert event.value == 1

    def test_key_event_value_up(self) -> None:
        """Test KeyEvent with value=0 (UP)."""
        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=0,
        )
        assert event.value == 0

    def test_key_event_value_down(self) -> None:
        """Test KeyEvent with value=1 (DOWN)."""
        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,
        )
        assert event.value == 1

    def test_key_event_value_repeat(self) -> None:
        """Test KeyEvent with value=2 (REPEAT)."""
        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=KEY_EVENT_VALUE_REPEAT,
        )
        assert event.value == KEY_EVENT_VALUE_REPEAT

    def test_key_event_invalid_value_negative(self) -> None:
        """Test KeyEvent rejects value < 0."""
        with pytest.raises(ValidationError):  # ValidationError
            KeyEvent(
                kind=InputKind.KEY,
                device="/dev/input/event0",
                timestamp=1234567890.0,
                code=1,
                code_name="KEY_A",
                value=-1,  # Invalid
            )

    def test_key_event_invalid_value_too_large(self) -> None:
        """Test KeyEvent rejects value > 2."""
        with pytest.raises(ValidationError):  # ValidationError
            KeyEvent(
                kind=InputKind.KEY,
                device="/dev/input/event0",
                timestamp=1234567890.0,
                code=1,
                code_name="KEY_A",
                value=3,  # Invalid
            )

    def test_key_event_kind_must_be_key(self) -> None:
        """Test that KeyEvent.kind must be InputKind.KEY."""
        with pytest.raises(ValidationError):  # ValidationError
            KeyEvent(
                kind=InputKind.REL,  # type: ignore[arg-type]
                device="/dev/input/event0",
                timestamp=1234567890.0,
                code=1,
                code_name="KEY_A",
                value=1,
            )


class TestRelEvent:
    """Test RelEvent model."""

    def test_rel_event_creation(self) -> None:
        """Test creating a RelEvent."""
        event = RelEvent(
            kind=InputKind.REL,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=0,
            code_name="REL_X",
            value=REL_EVENT_VALUE,  # Movement
        )
        assert event.kind == InputKind.REL
        assert event.value == REL_EVENT_VALUE

    def test_rel_event_negative_value(self) -> None:
        """Test RelEvent accepts negative values."""
        event = RelEvent(
            kind=InputKind.REL,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=0,
            code_name="REL_X",
            value=REL_EVENT_NEGATIVE_VALUE,
        )
        assert event.value == REL_EVENT_NEGATIVE_VALUE

    def test_rel_event_kind_must_be_rel(self) -> None:
        """Test that RelEvent.kind must be InputKind.REL."""
        with pytest.raises(ValidationError):  # ValidationError
            RelEvent(
                kind=InputKind.KEY,  # type: ignore[arg-type]
                device="/dev/input/event0",
                timestamp=1234567890.0,
                code=0,
                code_name="REL_X",
                value=5,
            )


class TestAbsEvent:
    """Test AbsEvent model."""

    def test_abs_event_creation(self) -> None:
        """Test creating an AbsEvent."""
        event = AbsEvent(
            kind=InputKind.ABS,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=0,
            code_name="ABS_X",
            value=ABS_EVENT_VALUE,  # Position
        )
        assert event.kind == InputKind.ABS
        assert event.value == ABS_EVENT_VALUE

    def test_abs_event_zero_value(self) -> None:
        """Test AbsEvent with value=0."""
        event = AbsEvent(
            kind=InputKind.ABS,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=0,
            code_name="ABS_X",
            value=0,
        )
        assert event.value == 0

    def test_abs_event_large_value(self) -> None:
        """Test AbsEvent with large values."""
        event = AbsEvent(
            kind=InputKind.ABS,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=0,
            code_name="ABS_X",
            value=ABS_EVENT_MAX_VALUE,  # Max typical value
        )
        assert event.value == ABS_EVENT_MAX_VALUE

    def test_abs_event_kind_must_be_abs(self) -> None:
        """Test that AbsEvent.kind must be InputKind.ABS."""
        with pytest.raises(ValidationError):  # ValidationError
            AbsEvent(
                kind=InputKind.KEY,  # type: ignore[arg-type]
                device="/dev/input/event0",
                timestamp=1234567890.0,
                code=0,
                code_name="ABS_X",
                value=100,
            )


class TestInputEventDiscriminatedUnion:
    """Test InputEvent as discriminated union."""

    def test_input_event_deserialize_key_event(self) -> None:
        """Test deserializing a KeyEvent from InputEvent type."""
        data = {
            "kind": "KEY",
            "device": "/dev/input/event0",
            "timestamp": 1234567890.0,
            "code": 1,
            "code_name": "KEY_A",
            "value": 1,
        }
        # InputEvent should deserialize to KeyEvent
        # This uses Pydantic's discriminated union
        adapter: TypeAdapter[InputEvent] = TypeAdapter(InputEvent)
        event = adapter.validate_python(data)
        assert isinstance(event, KeyEvent)
        assert event.value == 1

    def test_input_event_deserialize_rel_event(self) -> None:
        """Test deserializing a RelEvent from InputEvent type."""
        data = {
            "kind": "REL",
            "device": "/dev/input/event0",
            "timestamp": 1234567890.0,
            "code": 0,
            "code_name": "REL_X",
            "value": 5,
        }
        adapter: TypeAdapter[InputEvent] = TypeAdapter(InputEvent)
        event = adapter.validate_python(data)
        assert isinstance(event, RelEvent)
        assert event.value == REL_EVENT_VALUE

    def test_input_event_deserialize_abs_event(self) -> None:
        """Test deserializing an AbsEvent from InputEvent type."""
        data = {
            "kind": "ABS",
            "device": "/dev/input/event0",
            "timestamp": 1234567890.0,
            "code": 0,
            "code_name": "ABS_X",
            "value": 100,
        }
        adapter: TypeAdapter[InputEvent] = TypeAdapter(InputEvent)
        event = adapter.validate_python(data)
        assert isinstance(event, AbsEvent)
        assert event.value == ABS_EVENT_VALUE

    def test_input_event_isinstance_checks(self) -> None:
        """Test using isinstance to check event types."""
        key_event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,
        )
        assert isinstance(key_event, KeyEvent)
        assert isinstance(key_event, BaseEvent)
        # Check that we can distinguish event types by their kind field
        assert key_event.kind == InputKind.KEY

    def test_events_are_immutable(self) -> None:
        """Test that all event types are immutable."""
        key_event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,
        )
        rel_event = RelEvent(
            kind=InputKind.REL,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=0,
            code_name="REL_X",
            value=5,
        )
        abs_event = AbsEvent(
            kind=InputKind.ABS,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=0,
            code_name="ABS_X",
            value=100,
        )

        for event in [key_event, rel_event, abs_event]:
            with pytest.raises(ValidationError):
                event.device = "/dev/input/event1"
