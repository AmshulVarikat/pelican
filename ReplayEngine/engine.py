from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Callable, Iterator, Optional, List
import queue

from .loader import ValidationDataset
from .modes import ReplayMode, ReplayOutputFormat
from .models import Alert


class ReplayEngine:
    def __init__(
        self,
        dataset: ValidationDataset,
        mode: ReplayMode = ReplayMode.SEQUENTIAL,
        output_format: ReplayOutputFormat = ReplayOutputFormat.RAW,
        acceleration_factor: float = 1.0,
    ) -> None:
        self.dataset = dataset
        self.mode = mode
        self.output_format = output_format
        self.acceleration_factor = acceleration_factor

        if self.acceleration_factor <= 0:
            raise ValueError("acceleration_factor must be greater than zero")

        # Callbacks and Queues for the push-based runner
        self._callbacks: List[Callable[[dict], None]] = []
        self._queues: List[queue.Queue] = []

        # Threading controls for background execution
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._is_running = False

    # ---------------------------------------------------------
    # Pull-based Generator Method
    # ---------------------------------------------------------
    def replay(self) -> Iterator[dict]:
        """
        Pull-based generator. Yields alerts sequentially, time-preserved, or accelerated.
        This ignores background thread controls (pause/stop) and executes synchronously in the caller's thread.
        """
        if self.mode is ReplayMode.SEQUENTIAL:
            yield from self._replay_sequential()
        elif self.mode is ReplayMode.TIME_PRESERVED:
            yield from self._replay_time_preserved()
        elif self.mode is ReplayMode.ACCELERATED:
            yield from self._replay_accelerated()
        else:
            raise NotImplementedError(f"Unsupported replay mode: {self.mode}")

    def _replay_sequential(self) -> Iterator[dict]:
        for alert in self.dataset.alerts:
            yield self._build_output(alert)

    def _replay_time_preserved(self) -> Iterator[dict]:
        previous_timestamp: datetime | None = None

        for alert in self.dataset.alerts:
            if previous_timestamp is not None:
                delay = (alert.timestamp - previous_timestamp).total_seconds()
                if delay > 0:
                    time.sleep(delay)
            previous_timestamp = alert.timestamp
            yield self._build_output(alert, replay_time=alert.timestamp)

    def _replay_accelerated(self) -> Iterator[dict]:
        previous_timestamp: datetime | None = None

        for alert in self.dataset.alerts:
            if previous_timestamp is not None:
                delay = (alert.timestamp - previous_timestamp).total_seconds() / self.acceleration_factor
                if delay > 0:
                    time.sleep(delay)
            previous_timestamp = alert.timestamp
            yield self._build_output(alert)

    # ---------------------------------------------------------
    # Push-based Subscription Methods
    # ---------------------------------------------------------
    def register_callback(self, callback: Callable[[dict], None]) -> None:
        """Register a function to be called when an alert is replayed."""
        self._callbacks.append(callback)

    def register_queue(self, q: queue.Queue) -> None:
        """Register a queue to which alerts will be pushed when replayed."""
        self._queues.append(q)

    # ---------------------------------------------------------
    # Push-based Background Execution Methods
    # ---------------------------------------------------------
    def start(self) -> None:
        """Starts the background replay engine."""
        if self._is_running:
            return
        self._is_running = True
        self._stop_event.clear()
        self._pause_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the background replay engine completely."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        self._is_running = False

    def pause(self) -> None:
        """Pauses the background replay engine."""
        self._pause_event.set()

    def resume(self) -> None:
        """Resumes the background replay engine."""
        self._pause_event.clear()

    def _wait_for_delay(self, delay: float) -> bool:
        """
        Waits for the specified delay in an interruptible way.
        Returns True if stop was requested, False otherwise.
        """
        while self._pause_event.is_set():
            if self._stop_event.is_set():
                return True
            time.sleep(0.1)
        
        if delay > 0:
            if self._stop_event.wait(timeout=delay):
                return True
                
        while self._pause_event.is_set():
            if self._stop_event.is_set():
                return True
            time.sleep(0.1)

        return False

    def _run_loop(self) -> None:
        previous_timestamp: datetime | None = None

        for alert in self.dataset.alerts:
            if self._stop_event.is_set():
                break

            delay = 0.0
            if previous_timestamp is not None:
                if self.mode is ReplayMode.TIME_PRESERVED:
                    delay = (alert.timestamp - previous_timestamp).total_seconds()
                elif self.mode is ReplayMode.ACCELERATED:
                    delay = (alert.timestamp - previous_timestamp).total_seconds() / self.acceleration_factor
            
            if self._wait_for_delay(delay):
                break

            previous_timestamp = alert.timestamp

            replay_time = alert.timestamp if self.mode is ReplayMode.TIME_PRESERVED else None
            output = self._build_output(alert, replay_time=replay_time)
            self._dispatch(output)

        self._is_running = False

    def _dispatch(self, output: dict) -> None:
        for cb in self._callbacks:
            try:
                cb(output)
            except Exception as e:
                print(f"Error in ReplayEngine callback: {e}")

        for q in self._queues:
            q.put(output)

    # ---------------------------------------------------------
    # Output Builder
    # ---------------------------------------------------------
    def _build_output(self, alert: Alert, replay_time: datetime | None = None) -> dict:
        replay_time = replay_time or datetime.now(timezone.utc)
        if self.output_format is ReplayOutputFormat.TEST:
            return {
                "alert": alert.raw_alert,
                "replay_time": replay_time.isoformat(),
                "source_dataset": self.dataset.dataset_name,
                "ground_truth": self._build_ground_truth_context(),
            }

        if self.output_format is ReplayOutputFormat.RAW:
            return {
                "alert": alert.raw_alert,
                "replay_time": replay_time.isoformat(),
            }

        raise NotImplementedError(f"Unsupported replay output format: {self.output_format}")

    def _build_ground_truth_context(self) -> dict:
        context = self.dataset.context
        if not context:
            return {}
        return {
            "start_time": context.start_time.isoformat() if context.start_time else None,
            "end_time": context.end_time.isoformat() if context.end_time else None,
            "asset": context.asset,
            "scenario_id": context.scenario_id,
            "attack_count": context.attack_count,
            "ground_truth_records": context.ground_truth_records,
            "execution_log_records": context.execution_log_records,
            "ground_truth_meta": context.ground_truth_meta,
        }