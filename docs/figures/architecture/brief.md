# Figure brief: runtime architecture

Status: layout approved by the user on October 25, 2026; final geometry verified below.

## Purpose and layout

README overview at approximately 920 px display width; English, at most 1,300 logical px,
minimum displayed text 8 px (target 10–12 px). Question: **what runs on B's computer, and
which data crosses into Twitch and OpenAI?** Deployment view, read left to right:

```text
                     B's Windows computer
                  ┌───────────────────────────┐
 Twitch events ──>│      Local service         │<──> OpenAI API
 Twitch Helix <──>│      · context + raid      │     transcription
                  │      · wave + estimates   │     + summaries
                  │          ↑ audio          │
                  │                           │
                  │ Studio <──> service ──> OBS│
                  │  preview / send   read-only│
                  │                           │
                  │ OS keyring    SQLite      │
                  └───────────────────────────┘
```

Final drawing uses distinct request/result lanes. Service → OBS means local overlay state;
OBS broadcasts B's scene. Chat publishing is a separate service → Twitch action. Adjust
exact geometry to remove crossings while retaining this deployment view.

## Visual direction

- White canvas and near-black ink from `frontend/src/studio.css`; a dark service emphasizes
  the local process. Grey lines encode transports. No decorative purple fills; only Twitch's
  official logo retains its purple. Other official marks retain their own colours.
- Inter matches the actual interface, without proprietary Roobert. Storage is secondary.
- Distinctive element: exact-preview studio and OBS as separate delivery surfaces; independent
  local-audio input rather than a misleading Twitch audio-download path.
- Unlike previous projects recorded in `taste.md`, no monitor wall, 3D scene or coloured grid.
  The local-machine boundary is the main organizing shape.
- Static SVG and 2× PNG for README, editable draw.io and vector PDF. Timing has its own figure.

## Source map

| Element or relationship | Actual source |
| --- | --- |
| Loopback FastAPI process | `src/raid_handshake/__main__.py:main`; `app.py:create_app`, `local_only` |
| Public Client login / token lifecycle | `twitch.py:Twitch.begin_device`, `_poll_device`, `access_token`, `_refresh` |
| Twitch → service: B's raid, chat, follow events | `twitch.py:Twitch.subscribe`, `run_events`; `service.py:Service.on_event` |
| Service ↔ Twitch: source metadata / clips | `twitch.py:Twitch.guest`; `service.py:Service._guest_context` |
| Service ↔ Twitch: complete Chatters polls | `twitch.py:Twitch.chatters`; `service.py:Service._poll_loop` |
| Service → Twitch: confirmed welcome | `service.py:Service.preview`, `send`; `twitch.py:Twitch.send_chat` |
| Selected local audio → service | `audio.py:AudioCapture._record`; `service.py:start_audio`, `_queue_audio` |
| Service ↔ OpenAI: WAV → transcript; transcript/chat → structured summary | `ai.py:OpenAIContext.transcribe`, `summarize`; `service.py:_transcription_loop`, `refresh_summary` |
| Studio ↔ service: actions / admin state | `app.py` REST routes, `updates`; `frontend/src/studio.ts:markPreview` and send handler |
| Service → OBS: filtered overlay state | `app.py:updates`; `service.py:state(overlay=True)`; `studio.ts:renderOverlay` |
| Rolling context / wave / connection estimates | `ai.py:Context`; `learning.py:WaveLearner`; `metrics.py:Metrics` |
| SQLite versus OS credentials | `storage.py:Store`; `credentials.py:Credentials`; `service.py:persist`, `_tick_loop` |

Do not draw a hosted app server, public webhook/tunnel, source-chat history API, verified
raider identities, implemented Shoutout feature, or Codex in the runtime path. Codex is the
development tool, not the runtime summarizer.

## Verification

October 25, 2026: `fig look --medium readme` reported no layout findings after correction.
All nine inspection tiles and the 920 px HTTP `<img>` preview from `fig show` were visually
reviewed. The draw.io/SVG XML, 2× PNG and single-page PDF were checked; PDF fonts are embedded.
The smallest declared text at README width is 9.88 px. Native draw.io shapes remain editable.
