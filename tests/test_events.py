
from remy.events import EventBus, EventType


async def test_publish_fans_out_to_all_subscribers():
    bus = EventBus()
    q1, q2 = bus.subscribe(), bus.subscribe()
    bus.publish(EventType.WAKE, score=0.9)
    assert (await q1.get()).data["score"] == 0.9
    assert (await q2.get()).data["score"] == 0.9


async def test_full_queue_drops_oldest_not_newest():
    bus = EventBus()
    q = bus.subscribe(maxsize=2)
    for i in range(5):
        bus.publish(EventType.AUDIO_LEVEL, rms=i)
    levels = [q.get_nowait().data["rms"] for _ in range(2)]
    assert levels == [3, 4]


async def test_threadsafe_publish_requires_bound_loop():
    bus = EventBus()
    try:
        bus.publish_threadsafe(EventType.WAKE)
        assert False, "should have raised"
    except RuntimeError:
        pass


async def test_event_to_json_shape():
    bus = EventBus()
    q = bus.subscribe()
    bus.publish(EventType.TRANSCRIPT, text="hello")
    ev = await q.get()
    payload = ev.to_json()
    assert payload["type"] == "transcript"
    assert payload["data"] == {"text": "hello"}
    assert isinstance(payload["ts"], float)


async def test_unsubscribe_stops_delivery():
    bus = EventBus()
    q = bus.subscribe()
    bus.unsubscribe(q)
    bus.publish(EventType.WAKE)
    assert q.empty()
