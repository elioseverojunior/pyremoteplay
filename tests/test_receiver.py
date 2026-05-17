"""Tests for `pyremoteplay.receiver.QueueReceiver`.

These tests exercise the public surface used by downstream consumers
(e.g., headless frame analyzers) without spinning up a real Remote Play
session — `av.VideoFrame.from_ndarray()` produces synthetic frames that
behave identically to decoded H.264 output for the purposes of the
queue/getter contract.
"""
from __future__ import annotations

import numpy as np
import pytest

av = pytest.importorskip("av")  # tests are skipped on installs without PyAV

from pyremoteplay.receiver import QueueReceiver


def _make_frame(seed: int, width: int = 16, height: int = 16) -> av.VideoFrame:
    """Build a deterministic synthetic RGB frame.

    Using a tiny resolution keeps tests fast and removes any dependency on
    real codec output.
    """
    rng = np.random.default_rng(seed)
    array = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    return av.VideoFrame.from_ndarray(array, format="rgb24")


class _StubSession:
    """Minimal Session double — `handle_video` only needs `.events.emit`."""

    def __init__(self) -> None:
        self.emitted: list[str] = []
        self.events = self

    def emit(self, name: str) -> None:
        self.emitted.append(name)


@pytest.fixture
def receiver_with_session() -> tuple[QueueReceiver, _StubSession]:
    """A receiver wired to a stub session, with `_session` set."""
    receiver = QueueReceiver(max_frames=3)
    session = _StubSession()
    receiver._session = session  # noqa: SLF001 -- public API does this indirectly
    return receiver, session


class TestQueueReceiverBasics:
    """Constructor, queue sizing, and empty-queue behavior."""

    def test_max_frames_minimum_is_one(self) -> None:
        """Max frames is clamped to >= 1, even with 0 or negative input."""
        receiver = QueueReceiver(max_frames=0)
        assert receiver._v_queue.maxlen == 1
        assert receiver._a_queue.maxlen == 1

    def test_default_max_frames(self) -> None:
        """Default max_frames=10 is applied to both queues."""
        receiver = QueueReceiver()
        assert receiver._v_queue.maxlen == 10
        assert receiver._a_queue.maxlen == 10

    def test_separate_video_audio_limits(self) -> None:
        """When set explicitly, video/audio limits diverge from max_frames."""
        receiver = QueueReceiver(max_frames=5, max_video_frames=20, max_audio_frames=2)
        assert receiver._v_queue.maxlen == 20
        assert receiver._a_queue.maxlen == 2

    def test_negative_overrides_use_max_frames(self) -> None:
        """Setting a -1 override falls back to max_frames (per docstring)."""
        receiver = QueueReceiver(max_frames=5, max_video_frames=-1, max_audio_frames=-1)
        assert receiver._v_queue.maxlen == 5
        assert receiver._a_queue.maxlen == 5

    def test_empty_queue_returns_none(self) -> None:
        """Getters return None when queues are empty."""
        receiver = QueueReceiver()
        assert receiver.get_video_frame() is None
        assert receiver.get_audio_frame() is None
        assert receiver.get_latest_video_frame() is None
        assert receiver.get_latest_audio_frame() is None


class TestQueueReceiverVideoQueue:
    """Frame ingestion, ordering, and FIFO/LIFO accessors."""

    def test_handle_video_appends_and_emits(
        self, receiver_with_session: tuple[QueueReceiver, _StubSession]
    ) -> None:
        """handle_video adds the frame and fires the `video_frame` event."""
        receiver, session = receiver_with_session
        frame = _make_frame(seed=1)
        receiver.handle_video(frame)

        assert len(receiver._v_queue) == 1
        assert receiver._v_queue[0] is frame
        assert session.emitted == ["video_frame"]

    def test_get_video_frame_returns_oldest(
        self, receiver_with_session: tuple[QueueReceiver, _StubSession]
    ) -> None:
        """get_video_frame returns the FIFO head."""
        receiver, _ = receiver_with_session
        first = _make_frame(seed=1)
        second = _make_frame(seed=2)
        receiver.handle_video(first)
        receiver.handle_video(second)

        assert receiver.get_video_frame() is first

    def test_get_latest_video_frame_returns_newest(
        self, receiver_with_session: tuple[QueueReceiver, _StubSession]
    ) -> None:
        """get_latest_video_frame returns the LIFO tail — what we use for coaching."""
        receiver, _ = receiver_with_session
        first = _make_frame(seed=1)
        second = _make_frame(seed=2)
        third = _make_frame(seed=3)
        receiver.handle_video(first)
        receiver.handle_video(second)
        receiver.handle_video(third)

        assert receiver.get_latest_video_frame() is third

    def test_queue_overflow_drops_oldest(
        self, receiver_with_session: tuple[QueueReceiver, _StubSession]
    ) -> None:
        """Exceeding max_video_frames drops the oldest entry (deque semantics)."""
        receiver, _ = receiver_with_session  # max_frames=3
        frames = [_make_frame(seed=i) for i in range(5)]
        for frame in frames:
            receiver.handle_video(frame)

        # After 5 puts into a size-3 queue, oldest 2 are dropped
        assert len(receiver._v_queue) == 3
        assert receiver.get_video_frame() is frames[2]
        assert receiver.get_latest_video_frame() is frames[4]

    def test_video_frames_property_returns_snapshot(
        self, receiver_with_session: tuple[QueueReceiver, _StubSession]
    ) -> None:
        """`video_frames` returns an ordered list snapshot of the queue."""
        receiver, _ = receiver_with_session
        frames = [_make_frame(seed=i) for i in range(2)]
        for frame in frames:
            receiver.handle_video(frame)

        snapshot = receiver.video_frames
        assert isinstance(snapshot, list)
        assert snapshot == frames

    def test_snapshot_does_not_share_state(
        self, receiver_with_session: tuple[QueueReceiver, _StubSession]
    ) -> None:
        """Mutating the returned snapshot does not affect the internal queue."""
        receiver, _ = receiver_with_session
        receiver.handle_video(_make_frame(seed=1))
        snapshot = receiver.video_frames

        snapshot.clear()
        assert len(receiver._v_queue) == 1  # internal queue intact


class TestFrameNdarrayConversion:
    """Round-trip a frame through ndarray — the path the coach uses for vision."""

    def test_video_frame_to_ndarray_rgb24(self) -> None:
        """av.VideoFrame.to_ndarray returns (H, W, 3) uint8 for rgb24 format."""
        frame = _make_frame(seed=42, width=32, height=24)
        array = frame.to_ndarray(format="rgb24")

        assert array.shape == (24, 32, 3)
        assert array.dtype == np.uint8

    def test_video_frame_roundtrip_preserves_pixels(self) -> None:
        """Encoding then decoding via ndarray preserves pixel values."""
        original = np.full((8, 8, 3), 128, dtype=np.uint8)
        original[0, 0] = [255, 0, 0]
        original[7, 7] = [0, 255, 0]

        frame = av.VideoFrame.from_ndarray(original, format="rgb24")
        decoded = frame.to_ndarray(format="rgb24")

        np.testing.assert_array_equal(decoded, original)


class TestQueueReceiverClose:
    """Lifecycle: close() must drain both queues."""

    def test_close_clears_queues(
        self, receiver_with_session: tuple[QueueReceiver, _StubSession]
    ) -> None:
        receiver, _ = receiver_with_session
        receiver.handle_video(_make_frame(seed=1))

        receiver.close()

        assert receiver.get_video_frame() is None
        assert receiver.get_audio_frame() is None
        assert len(receiver._v_queue) == 0
        assert len(receiver._a_queue) == 0
