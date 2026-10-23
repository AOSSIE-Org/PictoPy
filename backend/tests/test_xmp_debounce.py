import threading
import time
from concurrent.futures import Future
from typing import Any, List

from app.utils.xmp.debounce import ExportDebouncer

DELAY = 0.05


class FakeExecutor:
    """Hands out futures the test moves through queued → running → done."""

    def __init__(self) -> None:
        self.futures: List["Future[Any]"] = []
        self.fail = False
        self.lock = threading.Lock()

    def submit(self) -> "Future[Any]":
        if self.fail:
            raise RuntimeError("executor is shut down")
        future: "Future[Any]" = Future()
        with self.lock:
            self.futures.append(future)
        return future


def _settle() -> None:
    time.sleep(DELAY * 4)


def test_a_burst_of_edits_becomes_one_pass():
    executor = FakeExecutor()
    debouncer = ExportDebouncer(executor.submit, delay=DELAY)
    for _ in range(20):
        debouncer.notify()
    _settle()
    assert len(executor.futures) == 1


def test_the_pass_starts_after_the_last_edit():
    executor = FakeExecutor()
    debouncer = ExportDebouncer(executor.submit, delay=DELAY * 4)
    for _ in range(5):
        debouncer.notify()
        time.sleep(DELAY)  # keeps restarting the countdown
    assert executor.futures == []
    time.sleep(DELAY * 8)
    assert len(executor.futures) == 1


def test_a_pass_still_queued_absorbs_later_edits():
    executor = FakeExecutor()
    debouncer = ExportDebouncer(executor.submit, delay=DELAY)
    debouncer.notify()
    _settle()
    debouncer.notify()  # first pass hasn't started: it will see this edit
    _settle()
    assert len(executor.futures) == 1


def test_an_edit_during_a_running_pass_gets_its_own_pass():
    executor = FakeExecutor()
    debouncer = ExportDebouncer(executor.submit, delay=DELAY)
    debouncer.notify()
    _settle()
    assert executor.futures[0].set_running_or_notify_cancel()
    debouncer.notify()  # the running pass may already be past this image
    _settle()
    assert len(executor.futures) == 2


def test_an_edit_after_a_finished_pass_gets_a_new_one():
    executor = FakeExecutor()
    debouncer = ExportDebouncer(executor.submit, delay=DELAY)
    debouncer.notify()
    _settle()
    executor.futures[0].set_running_or_notify_cancel()
    executor.futures[0].set_result(None)
    debouncer.notify()
    _settle()
    assert len(executor.futures) == 2


def test_a_failed_submit_is_swallowed_and_the_next_edit_retries():
    executor = FakeExecutor()
    debouncer = ExportDebouncer(executor.submit, delay=DELAY)
    executor.fail = True
    debouncer.notify()
    _settle()
    executor.fail = False
    debouncer.notify()
    _settle()
    assert len(executor.futures) == 1


def test_closing_cancels_a_pending_pass_and_ignores_later_edits():
    executor = FakeExecutor()
    debouncer = ExportDebouncer(executor.submit, delay=DELAY)
    debouncer.notify()
    debouncer.close()
    debouncer.notify()
    _settle()
    assert executor.futures == []


def test_concurrent_edits_from_many_threads_still_make_one_pass():
    executor = FakeExecutor()
    debouncer = ExportDebouncer(executor.submit, delay=DELAY * 2)
    threads = [threading.Thread(target=debouncer.notify) for _ in range(50)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    time.sleep(DELAY * 6)
    assert len(executor.futures) == 1
