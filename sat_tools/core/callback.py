"""
Callback Module

Provides callback mechanism for bake operations,
allowing integration with upload and other post-processing.
"""

from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import threading
import queue


class CallbackType(str, Enum):
    """Types of callbacks."""
    ON_SUCCESS = "on_success"
    ON_ERROR = "on_error"
    ON_PROGRESS = "on_progress"
    ON_COMPLETE = "on_complete"


@dataclass
class BakeCallback:
    """Represents a callback function."""
    callback_type: CallbackType
    handler: Callable[[Dict[str, Any]], None]
    name: str = ""
    
    def invoke(self, data: Dict[str, Any]):
        """Invoke the callback with data."""
        try:
            self.handler(data)
        except Exception as e:
            print(f"Callback error ({self.name}): {e}")


class CallbackManager:
    """
    Manages callbacks for bake operations.
    
    Allows registering callbacks for different events
    (success, error, progress) and invokes them when appropriate.
    """
    
    def __init__(self):
        """Initialize the callback manager."""
        self._callbacks: Dict[CallbackType, List[BakeCallback]] = {
            CallbackType.ON_SUCCESS: [],
            CallbackType.ON_ERROR: [],
            CallbackType.ON_PROGRESS: [],
            CallbackType.ON_COMPLETE: [],
        }
        self._async_queue: Optional[queue.Queue] = None
        self._async_thread: Optional[threading.Thread] = None
    
    def register(
        self,
        callback_type: CallbackType,
        handler: Callable[[Dict[str, Any]], None],
        name: str = ""
    ) -> BakeCallback:
        """
        Register a callback.
        
        Args:
            callback_type: Type of callback.
            handler: Callback function.
            name: Optional name for the callback.
            
        Returns:
            The created BakeCallback.
        """
        callback = BakeCallback(
            callback_type=callback_type,
            handler=handler,
            name=name or f"{callback_type.value}_{len(self._callbacks[callback_type])}"
        )
        self._callbacks[callback_type].append(callback)
        return callback
    
    def on_success(self, handler: Callable[[Dict[str, Any]], None], name: str = "") -> BakeCallback:
        """Register a success callback."""
        return self.register(CallbackType.ON_SUCCESS, handler, name)
    
    def on_error(self, handler: Callable[[Dict[str, Any]], None], name: str = "") -> BakeCallback:
        """Register an error callback."""
        return self.register(CallbackType.ON_ERROR, handler, name)
    
    def on_progress(self, handler: Callable[[Dict[str, Any]], None], name: str = "") -> BakeCallback:
        """Register a progress callback."""
        return self.register(CallbackType.ON_PROGRESS, handler, name)
    
    def on_complete(self, handler: Callable[[Dict[str, Any]], None], name: str = "") -> BakeCallback:
        """Register a completion callback (called after success or error)."""
        return self.register(CallbackType.ON_COMPLETE, handler, name)
    
    def unregister(self, callback: BakeCallback):
        """Unregister a callback."""
        if callback.callback_type in self._callbacks:
            self._callbacks[callback.callback_type] = [
                c for c in self._callbacks[callback.callback_type]
                if c != callback
            ]
    
    def clear(self, callback_type: Optional[CallbackType] = None):
        """Clear callbacks."""
        if callback_type:
            self._callbacks[callback_type] = []
        else:
            for ct in self._callbacks:
                self._callbacks[ct] = []
    
    def invoke(self, callback_type: CallbackType, data: Dict[str, Any]):
        """
        Invoke all callbacks of a given type.
        
        Args:
            callback_type: Type of callbacks to invoke.
            data: Data to pass to callbacks.
        """
        for callback in self._callbacks[callback_type]:
            callback.invoke(data)
    
    def invoke_success(self, data: Dict[str, Any]):
        """Invoke success callbacks."""
        self.invoke(CallbackType.ON_SUCCESS, data)
        self.invoke(CallbackType.ON_COMPLETE, {**data, 'status': 'success'})
    
    def invoke_error(self, data: Dict[str, Any]):
        """Invoke error callbacks."""
        self.invoke(CallbackType.ON_ERROR, data)
        self.invoke(CallbackType.ON_COMPLETE, {**data, 'status': 'error'})
    
    def invoke_progress(self, data: Dict[str, Any]):
        """Invoke progress callbacks."""
        self.invoke(CallbackType.ON_PROGRESS, data)
    
    def start_async_processing(self):
        """Start async callback processing."""
        if self._async_thread is not None:
            return
            
        self._async_queue = queue.Queue()
        self._async_thread = threading.Thread(target=self._async_worker, daemon=True)
        self._async_thread.start()
    
    def _async_worker(self):
        """Worker thread for async callback processing."""
        while True:
            try:
                callback_type, data = self._async_queue.get(timeout=1.0)
                if callback_type is None:
                    break
                self.invoke(callback_type, data)
            except queue.Empty:
                continue
    
    def queue_async(self, callback_type: CallbackType, data: Dict[str, Any]):
        """Queue a callback for async processing."""
        if self._async_queue is not None:
            self._async_queue.put((callback_type, data))
    
    def stop_async_processing(self):
        """Stop async callback processing."""
        if self._async_queue is not None:
            self._async_queue.put((None, None))
        if self._async_thread is not None:
            self._async_thread.join(timeout=5.0)
            self._async_thread = None
            self._async_queue = None


# Global callback manager instance
_global_callback_manager: Optional[CallbackManager] = None


def get_callback_manager() -> CallbackManager:
    """Get the global callback manager instance."""
    global _global_callback_manager
    if _global_callback_manager is None:
        _global_callback_manager = CallbackManager()
    return _global_callback_manager


def on_bake_success(handler: Callable[[Dict[str, Any]], None], name: str = ""):
    """Decorator to register a success callback."""
    get_callback_manager().on_success(handler, name)
    return handler


def on_bake_error(handler: Callable[[Dict[str, Any]], None], name: str = ""):
    """Decorator to register an error callback."""
    get_callback_manager().on_error(handler, name)
    return handler
