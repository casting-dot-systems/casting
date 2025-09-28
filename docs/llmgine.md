# LLMgine Message Bus & App Development Guide

This document is a comprehensive guide to building engines and applications on top of **LLMgine** using its production-ready message bus. It covers the **core API**, **filters**, **middleware**, **resilience features** (retries, dead letter queue, circuit breakers, backpressure), **metrics**, **observability**, and **persistence**. It ends with a **UI-free Tool Chat Engine** sample.

---

## 1) Core mental model

- **Command** (`llmgine.messages.commands.Command`)
  - Represents an *action to perform*.
  - Each command is handled by **exactly one** command handler.
  - Executed via `MessageBus.execute(command) -> CommandResult`.

- **Event** (`llmgine.messages.events.Event`)
  - Represents *something that happened*.
  - May be handled by **many** event handlers.
  - Published via `MessageBus.publish(event)`.

- **Session** (`llmgine.llm.SessionID`)
  - Scopes handlers & events to a logical conversation / engine instance.
  - Handlers can be **bus-scoped** (default `"BUS"`) or **session-scoped** (a specific `SessionID`).
  - Use sessions to automatically register/unregister handlers and emit start/end events.

---

## 2) Bus implementations

### `MessageBus` (default)
`llmgine.bus.bus.MessageBus` provides:
- Async processing with batching
- Middleware & filter chains
- Session-scoped handler management
- Optional event persistence for scheduled events
- Observability hooks

### `ResilientMessageBus`
`llmgine.bus.resilience.ResilientMessageBus` adds:
- **Bounded queue** + **backpressure** (`BackpressureStrategy`)
- **Retry logic** for command failures
- **Dead-letter queue** (DLQ)
- **Circuit breaker** per command type
- Queue metrics & breaker state inspection

Import shortcut:
```python
from llmgine.bus import MessageBus, ResilientMessageBus, BackpressureStrategy
````

---

## 3) Quick start

```python
import asyncio
from dataclasses import dataclass
from llmgine.bus import MessageBus
from llmgine.llm import SessionID
from llmgine.messages.commands import Command, CommandResult
from llmgine.messages.events import Event

# 1) Define your domain messages
@dataclass
class HelloCommand(Command):
    name: str = "world"

@dataclass
class HelloEvent(Event):
    text: str = "hello!"

# 2) Create bus and register handlers
bus = MessageBus()

async def handle_hello_command(cmd: HelloCommand) -> CommandResult:
    # Do work...
    await bus.publish(HelloEvent(text=f"Hello, {cmd.name}!"), await_processing=False)
    return CommandResult(success=True, result=f"Greeted {cmd.name}")

bus.register_command_handler(HelloCommand, handle_hello_command)

async def on_hello_event(evt: HelloEvent) -> None:
    print(f"[event] {evt.text}")

bus.register_event_handler(HelloEvent, on_hello_event)

# 3) Start, execute, and stop
async def main():
    await bus.start()
    result = await bus.execute(HelloCommand(name="LLMgine"))
    print(result)
    await bus.stop()

asyncio.run(main())
```

**Notes**

* `publish(event, await_processing=True)` waits until the queue drains for that event batch. Set `await_processing=False` for fire-and-forget.
* Use `await bus.wait_for_events()` to await the current queue.

---

## 4) Sessions

Use sessions to scope handlers and lifecycle events:

```python
import asyncio
from llmgine.bus import MessageBus
from llmgine.bus.session import SessionStartEvent, SessionEndEvent
from llmgine.llm import SessionID

bus = MessageBus()

async def on_session_start(evt: SessionStartEvent): print("session start:", evt.session_id)
async def on_session_end(evt: SessionEndEvent): print("session end:", evt.session_id)

bus.register_event_handler(SessionStartEvent, on_session_start)
bus.register_event_handler(SessionEndEvent, on_session_end)

async def main():
    await bus.start()
    # Option A: managed by bus
    async with bus.session() as sess:
        # `sess.session_id` is usable to register per-session handlers
        pass

    # Option B: use BusSession directly
    from llmgine.bus.session import BusSession
    async with BusSession() as sess:
        # Register handlers bound to this session:
        def echo_handler(evt): ...
        sess.register_event_handler(SessionStartEvent, on_session_start)
        sess.register_event_handler(SessionEndEvent, on_session_end)
    await bus.stop()

asyncio.run(main())
```

### Session-scoped handlers

Register handlers with a specific `SessionID` to isolate them:

```python
from llmgine.llm import SessionID
bus.register_event_handler(MyEvent, my_handler, session_id=SessionID("abc123"))
```

Handlers are automatically unregistered at session end.

---

## 5) Handler registration & priority

* **Bus-wide** (default): `session_id=SessionID("BUS")`
* **Session-scoped**: provide a concrete `SessionID`

Event handlers may have **priorities** via `HandlerPriority`:

```python
from llmgine.bus.interfaces import HandlerPriority
bus.register_event_handler(MyEvent, high_handler, priority=HandlerPriority.HIGH)
```

Handlers run in ascending priority (HIGHEST=0 first), by groups.

---

## 6) Filters and middleware

### Filters (`llmgine.bus.filters`)

Filters decide whether an event should be handled:

* `SessionFilter`
* `EventTypeFilter`
* `PatternFilter`
* `MetadataFilter`
* `RateLimitFilter` (token bucket)
* `CompositeFilter`
* `DebugFilter`

```python
from llmgine.bus.filters import EventTypeFilter, RateLimitFilter, CompositeFilter
from llmgine.messages.events import Event

class MyEvent(Event): ...

bus.add_event_filter(
    CompositeFilter([
        EventTypeFilter(include_types={MyEvent}),
        RateLimitFilter(max_per_second=20, per_session=True)
    ])
)
```

### Middleware (`llmgine.bus.middleware`)

Middleware wraps handler execution for logging, timing, validation, retries, and rate‑limits:

* `LoggingMiddleware`
* `TimingMiddleware`
* `ValidationMiddleware`
* `RateLimitMiddleware`
* `RetryMiddleware` (commands only; not the same as the resilient bus retries)

```python
from llmgine.bus.middleware import LoggingMiddleware, ValidationMiddleware

bus.add_command_middleware(LoggingMiddleware())
bus.add_command_middleware(ValidationMiddleware(validate_session_id=True))
bus.add_event_middleware(LoggingMiddleware())
```

---

## 7) Resilience & throughput

Use `ResilientMessageBus` for production loads:

```python
from llmgine.bus import ResilientMessageBus, BackpressureStrategy

bus = ResilientMessageBus(
    event_queue_size=10000,
    backpressure_strategy=BackpressureStrategy.DROP_OLDEST,  # or REJECT_NEW / ADAPTIVE_RATE_LIMIT
)
await bus.start()
```

### Backpressure

* `DROP_OLDEST`: evict oldest to make room
* `REJECT_NEW`: reject incoming when full
* `ADAPTIVE_RATE_LIMIT`: progressively slow producers

Queue metrics:

```python
queue_stats = bus.get_queue_metrics()
# {'current_size': ..., 'total_enqueued': ..., 'total_dropped': ..., 'backpressure_active': ...}
```

### Command retries & DLQ

On failures, commands are retried (exponential backoff). After exhaustion, the command is added to a **dead letter queue** and a `DeadLetterCommandEvent` is published.

```python
entries = await bus.get_dead_letter_entries(limit=10)
# Retry a specific command by id:
await bus.retry_dead_letter_entry(command_id)
```

### Circuit breaker

Each command type has a circuit breaker. Inspect with:

```python
states = bus.get_circuit_breaker_states()
# {'MyCommand': {'state': 'closed|open|half_open', ...}}
```

---

## 8) Scheduling & persistence

### Scheduled events

Use `llmgine.messages.scheduled_events.ScheduledEvent` (or subclasses) to represent future events. The bus will requeue future events until `scheduled_time <= now`.

### Persistence (DB)

Best‑effort persistence for **scheduled events** (always on) and optional **event log** (off by default).

Environment variables:

* `LLMGINE_DB_URL` (default `sqlite:///./message_bus.db`)
* `LLMGINE_DB_SCHEMA` (default `message_bus`)
* `LLMGINE_PERSIST_EVENTS=1` enables logging of all events to `event_log`.

APIs:

```python
from llmgine.database import save_unfinished_events, get_and_delete_unfinished_events, persist_event
```

> The bus calls these as needed; you rarely call them directly.

---

## 9) Metrics

Use `llmgine.bus.metrics.get_metrics_collector()` or `bus.get_metrics()`:

* Counters: `events_published_total`, `events_processed_total`, `events_failed_total`, `commands_*`
* Histograms: `event_processing_duration_seconds`, `command_processing_duration_seconds` (p50/p95/p99)
* Gauges: `queue_size`, `backpressure_active`, `dead_letter_queue_size`, `registered_handlers`, etc.

```python
metrics = await bus.get_metrics()
print(metrics["counters"]["events_processed_total"])
```

---

## 10) Observability

### ObservabilityManager

Attach a manager to the bus for zero-overhead fanout to sinks:

```python
from llmgine.observability.manager import ObservabilityManager
from llmgine.observability.handlers.adapters import create_sync_console_handler, create_sync_file_handler

obs = ObservabilityManager()
obs.register_handler(create_sync_console_handler())
obs.register_handler(create_sync_file_handler(log_dir="logs"))
bus.set_observability_manager(obs)
```

### OpenTelemetry

If installed, `OpenTelemetryHandler` maps bus events to traces/spans:

* Sessions → root spans
* Commands → child spans
* Tool executions → spans
* Handler failures → exceptions on spans

```python
from llmgine.observability.otel_handler import OpenTelemetryHandler
obs.register_handler(OpenTelemetryHandler(service_name="llmgine"))
```

---

## 11) Tooling patterns (ToolManager, MCP)

`llmgine.llm.tools.tool_manager.ToolManager` provides:

* Auto schema generation from Python function signatures
* Argument coercion/validation
* Async execution & timeouts
* Optional MCP integration (graceful if deps absent)

```python
from llmgine.llm.tools.tool_manager import ToolManager

tm = ToolManager()
def get_weather(city: str) -> str: return f"Weather in {city} is sunny."

tm.register_tool(get_weather)
schemas = tm.parse_tools_to_list()  # OpenAI function-calling format
```

When your LLM returns tool calls (e.g., via litellm), convert to `ToolCall` and run:

```python
from llmgine.llm.tools import ToolCall
results = await tm.execute_tool_calls([ToolCall(id="1", name="get_weather", arguments='{"city":"Paris"}')])
```

---

## 12) API reference (selected)

### MessageBus

* `start() / stop() / reset()`
* `execute(command: Command) -> CommandResult`
* `publish(event: Event, await_processing=True) -> None`
* `wait_for_events()`
* Middleware: `add_command_middleware()`, `add_event_middleware()`
* Filters: `add_event_filter()`
* Handlers: `register_command_handler()`, `register_event_handler()`, `unregister_session_handlers()`
* Batch tuning: `set_batch_processing(batch_size, batch_timeout)`
* Error surfacing: `suppress_event_errors() / unsuppress_event_errors()`
* Introspection: `get_stats()`, `get_metrics()`

### ResilientMessageBus

* Everything above, plus:

  * Bounded queue/backpressure (`BackpressureStrategy`)
  * Retry + DLQ: `get_dead_letter_entries()`, `retry_dead_letter_entry()`
  * Circuit breaker: `get_circuit_breaker_states()`
  * Queue metrics: `get_queue_metrics()`

### BusSession

* Context manager that emits `SessionStartEvent`/`SessionEndEvent`
* Convenience registration methods for per-session handlers
* `execute_with_session(command)` to inject the session id automatically

---

## 13) Headless Tool Chat Engine (example)

This is a UI‑free version of the provided `programs/engines/tool_chat_engine.py`, showing how to combine the bus, a chat history, tools, and litellm.

> See `examples/tool_chat_engine_headless.py` in this PR for a complete runnable script.

**Flow**:

1. Define command/event types for the engine.
2. Maintain a `SimpleChatHistory`.
3. Register tools with `ToolManager`.
4. On `ToolChatEngineCommand`, call the model via `litellm.acompletion` with tools.
5. If tool calls appear, execute them and then call the model again for a final response.
6. Emit status and tool result events on the bus.

---

## 14) Troubleshooting & tips

* **No handlers found**: ensure `register_*_handler` was called with the *correct session id* and that the bus has started.
* **Events not observed**: confirm filters are not overly restrictive; check `await_processing`.
* **Backpressure rejecting events**: inspect `bus.get_queue_metrics()` and consider a different strategy or scaling consumers.
* **Command errors swallowed**: call `bus.unsuppress_event_errors()` during development to surface handler errors to publishers.

---

## 15) Glossary

* **BUS scope**: default, global scope (`SessionID("BUS")`)
* **Session scope**: handlers/events bound to a specific conversation/engine instance
* **DLQ**: Dead Letter Queue for failed commands
* **MCP**: Model Context Protocol for interop tooling

---

````

> 📄 **examples/tool_chat_engine_headless.py**

```python
"""
Headless Tool Chat Engine example (no UI).

Demonstrates:
- MessageBus lifecycle
- Custom command/event types for engine status
- SimpleChatHistory for context
- ToolManager for registering & executing tools
- Tool call round-trip with litellm
- Emitting tool execution & status events on the bus

Requires:
  pip install litellm
And configure your model via litellm environment variables as usual.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from litellm import acompletion

from llmgine.bus import MessageBus
from llmgine.llm import SessionID
from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools import ToolCall
from llmgine.llm.tools.tool_events import ToolExecuteResultEvent
from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.messages.commands import Command, CommandResult
from llmgine.messages.events import Event

# ------------------ Domain messages for the engine ------------------

@dataclass
class ToolChatEngineCommand(Command):
    prompt: str = ""

@dataclass
class ToolChatEngineStatusEvent(Event):
    status: str = ""

# ------------------ Demo tools ------------------

def get_weather(city: str) -> str:
    """Get current weather for a city (demo)."""
    return f"The weather in {city} is sunny and 72°F"

def calculate(expression: str) -> str:
    """Calculate a Python expression (demo)."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e!s}"

async def search_web(query: str) -> str:
    """Search the web (mock)."""
    await asyncio.sleep(0.1)
    return f"[mock] results for: {query}"

# ------------------ Engine ------------------

class ToolChatEngine:
    def __init__(self, model: str = "gpt-4o-mini", session_id: Optional[str] = None):
        self.session_id = SessionID(session_id or str(uuid.uuid4()))
        self.model = model
        self.bus = MessageBus()

        # Chat history: provider-agnostic; returns litellm-compatible messages
        self.chat = SimpleChatHistory(engine_id="tool_chat_engine", session_id=self.session_id)
        self.chat.set_system_prompt(
            "You are a helpful assistant with access to tools. "
            "Use tools when appropriate to help answer user questions."
        )

        # Tool manager
        self.tools = ToolManager()
        self.tools.register_tool(get_weather)
        self.tools.register_tool(calculate)
        self.tools.register_tool(search_web)

        self._log = logging.getLogger(__name__)

    async def handle(self, command: ToolChatEngineCommand) -> CommandResult:
        try:
            await self.bus.publish(ToolChatEngineStatusEvent(status="processing", session_id=self.session_id))

            # Add user message
            self.chat.add_user_message(command.prompt)

            # Prepare messages & tool schemas
            messages = self.chat.get_messages()
            tool_schemas = self.tools.parse_tools_to_list()

            await self.bus.publish(ToolChatEngineStatusEvent(status="calling LLM", session_id=self.session_id))

            # First call (let LLM decide about tools)
            response = await acompletion(model=self.model, messages=messages, tools=tool_schemas or None)

            if not response.choices:
                return CommandResult(success=False, error="No response from LLM")

            message = response.choices[0].message

            # If tool calls present, execute them and ask the model again
            if hasattr(message, "tool_calls") and message.tool_calls:
                await self.bus.publish(ToolChatEngineStatusEvent(status="executing tools", session_id=self.session_id))

                tool_calls = [
                    ToolCall(id=tc.id, name=tc.function.name, arguments=tc.function.arguments)
                    for tc in message.tool_calls
                ]

                results = []
                for tc in tool_calls:
                    result = await self.tools.execute_tool_call(tc)
                    results.append(result)
                    # Save tool result to chat and emit observability event
                    self.chat.add_assistant_message(content=message.content or "", tool_calls=tool_calls)
                    self.chat.add_tool_message(tool_call_id=tc.id, content=str(result))
                    # Emit a tool execution result event for observability
                    try:
                        args_obj = json.loads(tc.arguments) if isinstance(tc.arguments, str) else (tc.arguments or {})
                    except Exception:
                        args_obj = {"__raw__": tc.arguments}
                    await self.bus.publish(
                        ToolExecuteResultEvent(
                            execution_succeed=not str(result).startswith("Error"),
                            tool_info={"name": tc.name},
                            tool_args=args_obj,
                            tool_result=str(result),
                            tool_name=tc.name,
                            tool_call_id=tc.id,
                            engine_id="tool_chat_engine",
                            session_id=self.session_id,
                        ),
                        await_processing=False,
                    )

                # Final LLM response after tool results
                await self.bus.publish(ToolChatEngineStatusEvent(status="getting final response", session_id=self.session_id))
                final_messages = self.chat.get_messages()
                final = await acompletion(model=self.model, messages=final_messages)
                if final.choices and final.choices[0].message.content:
                    content = final.choices[0].message.content
                    self.chat.add_assistant_message(content)
                    await self.bus.publish(ToolChatEngineStatusEvent(status="finished", session_id=self.session_id))
                    return CommandResult(success=True, result=content)

            # No tool calls; return content directly
            content = message.content or ""
            self.chat.add_assistant_message(content)
            await self.bus.publish(ToolChatEngineStatusEvent(status="finished", session_id=self.session_id))
            return CommandResult(success=True, result=content)

        except Exception as e:
            await self.bus.publish(ToolChatEngineStatusEvent(status="finished", session_id=self.session_id))
            return CommandResult(success=False, error=str(e))

# ------------------ Entrypoint ------------------

async def main():
    logging.basicConfig(level=logging.INFO)
    engine = ToolChatEngine(model="gpt-4o-mini")

    # Start the bus (handlers may be added here if desired)
    await engine.bus.start()

    # Execute a sample command
    res = await engine.handle(ToolChatEngineCommand(prompt="What's the weather in Kyoto? Then calculate 12*12."))
    print("RESULT:", res)

    await engine.bus.stop()

if __name__ == "__main__":
    asyncio.run(main())
````