# remy_core

REMY's capability layer. `remy_ui` draws and speaks; this decides what REMY
actually does. Four verbs:

| Verb | What it is | You say |
|------|-----------|---------|
| Tell | read data, show it | "what have I been listening to" |
| Judge | rank your own data, no guessing | "my favorite Kanye songs" |
| Act | do something, after you say yes | "add dinner friday at 8pm" |
| Chain | string the others together, one yes | "playlist of my top Ye and play it" |

```
» my favorite Kanye songs
« Your most-played Kanye: Runaway, Stronger, and Power.

» add dinner with friends friday at 8pm
« Add "Dinner with friends" Friday Aug 7, 8 PM to 9 PM to your calendar. Sound good?
» yes
« Done. Dinner with friends is on for Friday Aug 7.
```

## A sentence in, the right verb out

The router reads a spoken line and picks the verb. No LLM in the hot path;
it's pattern matching, fast and deterministic. Anything it doesn't recognize
returns `None`, which is where the real REMY falls back to the local model.

```python
from remy_core.router import Router, execute

intent = Router().route("my favorite kanye songs", ctx)     # verb = "judge"
out    = execute(intent, ctx, {"spotify": spotify, "calendar": cal})

# Tell and Judge come back ready:  out.presentation   (draw it, say it)
# Act comes back on a leash:       out.pending        (say .confirm, wait, .run())
```

`route()` is pure, so classifying an intent is trivial to test. `execute()` is
the only thing that touches a client.

## Nothing fires without a yes

Every Act splits into three, and the gate sits in the gap:

```
parse(utterance)   ->  params      (or an error REMY can speak)
preview(params)    ->  the line REMY says out loud
execute(params)    ->  the effect  (only after you say yes)
```

```python
pending = plan(ACTIONS["calendar.add"], "add dinner with friends friday at 8pm", ctx)
pending.confirm                      # 'Add "Dinner with friends" ... Sound good?'
pending.run(FakeCalendarClient())    # only now does it happen
```

Chain works the same way, one gate for the whole thing. "Playlist of my
favorite Kanye and play it" runs the read step first, so REMY can show you the
seven tracks and count them in the question, then makes the playlist only
after you confirm.

Judge is real data only, on purpose. "Favorite Kanye" isn't REMY guessing your
taste. It's your top tracks, filtered to Ye, ranked by your actual plays. No
data, no answer, it just says so.

## Fake now, real on the Jetson

Every capability talks to an injected client, never a live API. Tests use
fakes that record the call. On the Jetson a real adapter wraps REMY's existing
Google and Spotify creds, twenty-odd lines each, and nothing above the client
changes. Time works the same way: `now` is injected through `RemyContext`, so
"friday at 8pm" resolves the same in a test as it does in the room.

## See it

```
python -m remy_core.demo    # one loop, all four verbs, plus a graceful miss

python remy_core/tests/test_datetime_parse.py
python remy_core/tests/test_calendar_add.py
python remy_core/tests/test_music.py
python remy_core/tests/test_router.py
python remy_core/tests/test_chain.py
```

## Layout

```
context.py      RemyContext: injected now, timezone, calendars
capability.py   the contracts, Result and Presentation, the gated driver
parse/          natural-language time to start/end. no deps, deterministic.
clients/        the seams: calendar and spotify, with fakes and adapter notes
actions/        Act:   calendar.add, spotify.create_playlist
providers/      Tell:  spotify.top_tracks
synthesizers/   Judge: spotify.favorite_by_artist
chains/         Chain: playlist_from_artist
router/         rules.py (the table) and the route/execute engine
music.py        tracks to a Ranking plus a spoken line
demo.py         the full loop
tests/          41 tests
```

## Not done yet

- Local-model fallback when the router returns `None`. Right now it just says
  it can't.
- Real Google and Spotify adapters behind the client seams.
- More capabilities on the same shape: `spotify.play`, `reminder.set`,
  `canvas.assignments`, `gmail.reply`.
