# Figure brief: one real raid

Status: layout approved by the user on October 25, 2026; final geometry verified below.

## Purpose and layout

Second README figure at approximately 920 px display width; English, at most 1,300 logical
px. Question: **what precedes and follows a raid in the default manual-send mode?** Five
participant columns; time runs down. Schematic, explicitly not to scale:

```text
Twitch       Local service       OpenAI       Studio       OBS
  │               │                │             │          │
  │<── polls ────>│<── audio/text ─>│             │          │ before
  │── raid ──────>│                              │          │
  │               │──────── guest facts ────────────────────>│
  │<── lookups ──>│──────── enriched card ───────────────────>│ parallel
  │               │──────── exact draft ────────>│          │
  │               │<──── preview + confirm ──────│          │
  │<── welcome ───│                              │          │
  │── chat ──────>│──────── wave update ─────────────────────>│ 0–60 s
  │<── polls ────>│                              │          │ 0–90 s
  │<── polls ────>│──────── connection sample ───────────────>│ 5/15/30 m
```

Label guest lookup and draft preparation as parallel, not sequential dependencies. Reuse the
prewarmed summary; a compact note explains refresh/blocked behavior without fresh speech.
The code's 60 s / 90 s / 5,15,30 min are observation windows, not network latency guarantees.
Do not draw the earlier 19.803-second result as a generic latency.

## Visual direction

Same white/ink/Inter family as architecture, with neutral lifelines, short message labels,
solid requests/events and dashed responses. Only the official Twitch logo is purple. A true
sequence layout, no repeated card-grid architecture and no large title banner. Static SVG,
2× PNG, editable draw.io and vector PDF.

## Source map

| Message / phase | Actual source |
| --- | --- |
| Pre-raid: audio → transcript → summary cache | `audio.py:AudioCapture._record`; `service.py:_transcription_loop`, `_summary_loop`; `ai.py:OpenAIContext` |
| Continuous complete Chatters polls, default 5 s | `service.py:_poll_loop`; `twitch.py:Twitch.chatters`; `config.py:ChannelConfig` |
| `channel.raid`, immediate source facts | `twitch.py:run_events`; `service.py:on_event`, `_tick_loop` |
| Concurrent guest lookup and landing preparation | `service.py:on_event` adjacent `_spawn(_guest_context)` / `_spawn(_landing)` |
| Source enrichment, budget 4.5 s | `service.py:_guest_context`; `twitch.py:guest` |
| Fresh summary reuse / refresh / blocked exception | `service.py:summary_ready`, `_landing`, `refresh_summary` |
| Draft → studio; preview acknowledgement → service | `service.py:notify`, `preview`; `app.py:updates`, `preview`; `studio.ts:markPreview` |
| Click / Ctrl+Shift+Enter → locked send → Twitch | `studio.ts` send handler; `hotkey.py`; `service.py:send`; `twitch.py:send_chat` |
| Sent text → read-only overlay | `service.py:state`; `studio.ts:renderOverlay` |
| First 60 s: B chat → wave learning | `service.py:on_event`, `_tick_loop`; `learning.py:WaveLearner` |
| First 90 s: S0-relative arrival union | `metrics.py:begin`, `_extend`, `advance` |
| 5/15/30 min: connection / speaker / channel-follow sample | `metrics.py:advance`; `studio.ts:metricsCard` |

No viewing-retention claim, verified raider list, automatic send in this default path, or
guaranteed network latency. Optional preapproved mode remains in README prose.

## Verification

October 25, 2026: `fig look --medium readme` reported no layout findings after correction.
All twelve inspection tiles and the 920 px HTTP `<img>` preview from `fig show` were visually
reviewed. Explanatory notes mask lifelines to avoid lines crossing text. The draw.io/SVG XML,
2× PNG and single-page PDF were checked; PDF fonts are embedded. The smallest declared text
at README width is 9.91 px. Lifeline crossings represent sequence notation, not extra receivers.
