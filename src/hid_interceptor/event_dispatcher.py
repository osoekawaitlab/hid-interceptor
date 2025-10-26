"""Event processing and hook execution."""

import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Any

from hid_interceptor.models import InputEvent

logger = logging.getLogger(__name__)

# Type alias for hook functions
HookFn = Callable[[InputEvent], Any]


class EventDispatcher:
    """Dispatches input events to registered hook functions.

    Responsibilities:
    - Execute hooks for each input event
    - Support both sync and async hook functions
    - Handle hook execution errors gracefully
    - Ensure all hooks are called even if one fails

    Attributes:
        _hooks: List of hook functions to call for each event
    """

    def __init__(self, hooks: list[HookFn] | None = None) -> None:
        """Initialize the event dispatcher.

        Args:
            hooks: Optional list of hook functions to register
        """
        self._hooks = hooks or []
        self._logger = logger

    def add_hook(self, hook: HookFn) -> None:
        """Register a new hook function.

        Args:
            hook: A callable that accepts an InputEvent
        """
        self._hooks.append(hook)
        hook_name = getattr(hook, "__name__", repr(hook))
        self._logger.debug("Registered hook: %s", hook_name)

    def remove_hook(self, hook: HookFn) -> None:
        """Unregister a hook function.

        Args:
            hook: The hook function to remove
        """
        if hook in self._hooks:
            self._hooks.remove(hook)
            hook_name = getattr(hook, "__name__", repr(hook))
            self._logger.debug("Unregistered hook: %s", hook_name)

    def get_hooks(self) -> list[HookFn]:
        """Get all registered hooks.

        Returns:
            List of hook functions
        """
        return list(self._hooks)

    async def dispatch(self, event: InputEvent) -> None:
        """Dispatch an input event to all registered hooks.

        Each hook is executed sequentially. If a hook raises an exception,
        the error is logged but other hooks continue to execute.

        Args:
            event: The input event to dispatch
        """
        for hook in self._hooks:
            await self._execute_hook(hook, event)

    async def _execute_hook(self, hook: HookFn, event: InputEvent) -> None:
        """Execute a single hook function.

        Automatically handles both sync and async hooks. Catches and logs
        any exceptions raised by the hook.

        Args:
            hook: The hook function to execute
            event: The input event to pass to the hook
        """
        hook_name = getattr(hook, "__name__", repr(hook))

        try:
            if inspect.iscoroutinefunction(hook):
                # Hook is async, await it
                await hook(event)
            else:
                # Hook is sync, run it in a thread pool
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, hook, event)
        except Exception:
            self._logger.exception("Error executing hook: %s", hook_name)
