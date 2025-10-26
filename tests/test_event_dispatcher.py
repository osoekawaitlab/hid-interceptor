"""Tests for event processing and hook execution."""

from collections.abc import Callable
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from hid_interceptor.event_dispatcher import EventDispatcher, HookFn
from hid_interceptor.models import InputEvent, InputKind, KeyEvent

# Test constants
EXPECTED_HOOK_COUNT = 2


class TestEventDispatcher:
    """Test the EventDispatcher class."""

    def test_init_empty(self) -> None:
        """Test creating dispatcher with no hooks."""
        dispatcher = EventDispatcher()
        assert dispatcher.get_hooks() == []

    def test_init_with_hooks(self) -> None:
        """Test creating dispatcher with initial hooks."""
        hook1: HookFn = MagicMock(spec=Callable[[InputEvent], None])
        hook2: HookFn = MagicMock(spec=Callable[[InputEvent], None])
        dispatcher = EventDispatcher(hooks=[hook1, hook2])

        hooks = dispatcher.get_hooks()
        assert len(hooks) == EXPECTED_HOOK_COUNT
        assert hook1 in hooks
        assert hook2 in hooks

    def test_add_hook(self) -> None:
        """Test adding a hook."""
        dispatcher = EventDispatcher()
        hook: HookFn = MagicMock(spec=Callable[[InputEvent], None])

        dispatcher.add_hook(hook)

        assert hook in dispatcher.get_hooks()

    def test_add_multiple_hooks(self) -> None:
        """Test adding multiple hooks."""
        dispatcher = EventDispatcher()
        hook1: HookFn = MagicMock(spec=Callable[[InputEvent], None])
        hook2: HookFn = MagicMock(spec=Callable[[InputEvent], None])

        dispatcher.add_hook(hook1)
        dispatcher.add_hook(hook2)

        hooks = dispatcher.get_hooks()
        assert len(hooks) == EXPECTED_HOOK_COUNT
        assert hook1 in hooks
        assert hook2 in hooks

    def test_remove_hook(self) -> None:
        """Test removing a hook."""
        dispatcher = EventDispatcher()
        hook: HookFn = MagicMock(spec=Callable[[InputEvent], None])
        dispatcher.add_hook(hook)

        dispatcher.remove_hook(hook)

        assert hook not in dispatcher.get_hooks()

    def test_remove_nonexistent_hook(self) -> None:
        """Test removing a hook that wasn't registered."""
        dispatcher = EventDispatcher()
        hook: HookFn = MagicMock(spec=Callable[[InputEvent], None])

        # Should not raise
        dispatcher.remove_hook(hook)

    def test_get_hooks_returns_copy(self) -> None:
        """Test that get_hooks returns a copy, not the internal list."""
        dispatcher = EventDispatcher()
        hook: HookFn = MagicMock(spec=Callable[[InputEvent], None])
        dispatcher.add_hook(hook)

        hooks1 = dispatcher.get_hooks()
        hooks2 = dispatcher.get_hooks()

        # Should be equal but not the same object
        assert hooks1 == hooks2
        assert hooks1 is not hooks2

    @pytest.mark.asyncio
    async def test_dispatch_sync_hook(self) -> None:
        """Test dispatching to a synchronous hook."""
        hook: HookFn = cast("HookFn", MagicMock(spec=Callable[[InputEvent], None]))
        dispatcher = EventDispatcher(hooks=[hook])

        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,
        )

        await dispatcher.dispatch(event)

        cast("MagicMock", hook).assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_dispatch_async_hook(self) -> None:
        """Test dispatching to an asynchronous hook."""
        hook = AsyncMock()
        dispatcher = EventDispatcher(hooks=[hook])

        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,
        )

        await dispatcher.dispatch(event)

        hook.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_dispatch_multiple_hooks(self) -> None:
        """Test dispatching to multiple hooks."""
        hook1: HookFn = cast("HookFn", MagicMock(spec=Callable[[InputEvent], None]))
        hook2: HookFn = cast("HookFn", AsyncMock(spec=Callable[[InputEvent], None]))
        hook3: HookFn = cast("HookFn", MagicMock(spec=Callable[[InputEvent], None]))
        dispatcher = EventDispatcher(hooks=[hook1, hook2, hook3])

        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,
        )

        await dispatcher.dispatch(event)

        cast("MagicMock", hook1).assert_called_once_with(event)
        cast("MagicMock", hook2).assert_called_once_with(event)
        cast("MagicMock", hook3).assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_dispatch_hook_exception_caught(self) -> None:
        """Test that hook exceptions are caught and logged."""
        hook1_mock = MagicMock(
            spec=Callable[[InputEvent], None],
            side_effect=ValueError("Test error"),
        )
        hook1: HookFn = cast("HookFn", hook1_mock)
        hook2: HookFn = cast("HookFn", MagicMock(spec=Callable[[InputEvent], None]))
        dispatcher = EventDispatcher(hooks=[hook1, hook2])

        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,
        )

        # Should not raise
        await dispatcher.dispatch(event)

        cast("MagicMock", hook1).assert_called_once_with(event)
        cast("MagicMock", hook2).assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_dispatch_async_hook_exception_caught(self) -> None:
        """Test that async hook exceptions are caught and logged."""

        async def failing_async_hook(_event: InputEvent) -> None:
            msg = "Hook failed"
            raise RuntimeError(msg)

        hook1: HookFn = failing_async_hook
        hook2: HookFn = cast("HookFn", MagicMock(spec=Callable[[InputEvent], None]))
        dispatcher = EventDispatcher(hooks=[hook1, hook2])

        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,
        )

        # Should not raise
        await dispatcher.dispatch(event)

        cast("MagicMock", hook2).assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_dispatch_no_hooks(self) -> None:
        """Test dispatching when no hooks are registered."""
        dispatcher = EventDispatcher()

        event = KeyEvent(
            kind=InputKind.KEY,
            device="/dev/input/event0",
            timestamp=1234567890.0,
            code=1,
            code_name="KEY_A",
            value=1,
        )

        # Should not raise
        await dispatcher.dispatch(event)
