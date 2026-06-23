# Replay Engine

Standalone replay layer for feeding JSON alerts (e.g., Wazuh alerts) into downstream modules.

## Features

- **Sequential, Time-Preserved, and Accelerated** replay modes.
- **Push-based Runner**: An event-driven background thread that pushes alerts to queues or callbacks, supporting pause, resume, and stop controls.
- **Pull-based Generator**: A simple synchronous generator for sequentially iterating over alerts.
- **Dynamic File Loading**: Point the engine to a single JSON file or a directory containing multiple JSON files, and it will load and sort all alerts chronologically.
- **Optional Context**: Supports loading ground truth or execution log context if requested.

## Setup and Initialization

Use the `create_engine` factory function to quickly set up a ready-to-use engine instance:

```python
from ReplayEngine import create_engine, ReplayMode

engine = create_engine(
    filepath="path/to/your/alerts_folder",  # Defaults to 'inputs' if omitted
    include_ground_truth=False,             # Set to True if you need context metadata
    mode=ReplayMode.TIME_PRESERVED          # Options: TIME_PRESERVED, SEQUENTIAL, ACCELERATED
)
```

## Usage: Push-Based Runner (Event-Driven)

The push-based runner executes the replay in a background thread. It is ideal for real-time systems where you want the engine to automatically fire events to downstream modules while keeping your main thread free.

### 1. Registering Hooks

You can register callback functions or standard thread-safe queues.

```python
import queue

# Using a callback
def on_alert(envelope):
    print("Received alert at:", envelope["replay_time"])

engine.register_callback(on_alert)

# Using a queue
alert_queue = queue.Queue()
engine.register_queue(alert_queue)
```

### 2. Controlling Playback

The engine exposes thread-safe methods to control the background replay loop:

```python
# Start the background thread
engine.start()

# Pause execution indefinitely
engine.pause()

# Resume execution from where it paused
engine.resume()

# Stop the engine completely (cannot be resumed, exits thread)
engine.stop()
```

When using a Queue, you can retrieve alerts in your own worker threads:
```python
while True:
    try:
        envelope = alert_queue.get(timeout=1.0)
        # process envelope
    except queue.Empty:
        # Check if engine is still running or handle timeout
        pass
```

## Usage: Pull-Based Generator (Synchronous)

If you don't need real-time pausing/stopping or background execution, you can use the built-in python generator. This method blocks the calling thread during time-preserved delays.

```python
from ReplayEngine import create_engine, ReplayMode

engine = create_engine(filepath="inputs", mode=ReplayMode.SEQUENTIAL)

for envelope in engine.replay():
    # Loop blocks until the next alert is yielded
    print(envelope["alert"]["id"])
```

## Output Shape

Each replayed item is emitted as a dictionary wrapper (envelope).

In `RAW` output format (default):
```json
{
  "alert": { ... raw alert JSON ... },
  "replay_time": "2026-06-12T00:00:00+00:00"
}
```

In `TEST` output format, it adds `source_dataset` and `ground_truth`.
In `TIME_PRESERVED` mode, `replay_time` reflects the source alert timestamp. In other modes, it is the emission timestamp.