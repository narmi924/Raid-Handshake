# Verification status

User story: a real Twitch raid reaches the local EventSub listener, source context appears in OBS,
OpenAI summarizes authorized recent audio/chat into a landing card, and the broadcaster confirms
or enables template posting before estimated chat-connection observations appear.

## Verified locally

- Final local automated run: **50 passed**, with one upstream Starlette/httpx deprecation warning.
  Ruff checks and the TypeScript/production frontend build pass.
- Python dependencies installed in the project's Python 3.11 virtual environment; no global
  faster-whisper/Ollama/model runtime installed.
- TypeScript checks and the Vite production build pass.
- FastAPI is running on `http://127.0.0.1:8765`; `/api/health` reports healthy.
- Real Chromium loads the control room, connects to its WebSocket and renders the disconnected
  onboarding state. It enumerates eight local audio-input options, including the default.
- Initial browser layout has no horizontal overflow. The control-room screenshot is a local
  setup-state screenshot, not demonstration evidence of a raid.
- The real Chromium OBS page connects to the overlay WebSocket and displays its standby state;
  computed backgrounds of both the HTML canvas and body are transparent (`rgba(0, 0, 0, 0)`).
- Clicking Start audio with no API key displays the expected configuration error and leaves
  capture off; automatic template mode is off and chat sending is disabled without a real draft.
- Automated tests cover baseline/differential cohort semantics, delayed events, pagination,
  stale/missing observations, native-emote ownership and unverified text, public DCF refresh,
  exact previews, duplicate send protection, uncertain delivery, data exposure and audio format.

## Live verification — 2026-10-25

Read-only inspection of the running local service and saved OBS configuration confirmed:

- The user is broadcasting A `thisisraida` from a phone and B `thisisraidb` from OBS.
  Twitch Public Client authorization is bound to B; EventSub and complete Get Chatters polling
  are connected without reported errors.
- Three incoming Twitch EventSub raid notifications from A were received at **16:33:08**,
  **16:41:21** and **16:51:46 Singapore time (UTC+08:00)**. Each reported one raid participant.
- Live OpenAI transcription matches the MP3 actually played by B's HTML browser source;
  the live summary and its transcript evidence were produced successfully. This was an API
  call against the configured project, not the local test fixtures.
- A manually confirmed landing card for the second raid has status `sent` and Twitch message
  ID `f3f5d26f-955d-44a1-a06e-85d5f0ebab92`. Local receipt-to-success elapsed time was
  **129.1 seconds**. Capture started after the raid, so this does **not** meet the 30-second goal.
- The first raid's real five-minute sample completed 0.52 seconds after its scheduled time:
  differential cohort R = 0, connected = 0, distinct speakers = 0, whole-channel follows = 0;
  both cohort and chat completeness flags were true, with no sample error. This verifies
  elapsed sampling for an empty cohort; it does not verify a positive cohort or viewer retention.
- The second raid's 60-second wave result is `insufficient`: one observed message from one
  author, no qualifying source-owned emotes or repeated text. A has no available recent clips.
- Saved OBS configuration contains the HTML browser source and a separate localhost overlay
  browser source. Desktop audio captures EDIFIER output, and the physical microphone is muted.
  Saved configuration alone does not prove the card's visibility in the delivered Twitch video.
- Capture was stopped when inspected after the second raid's successful transcription. The
  third raid followed a fresh transcript/summary with capture kept running, as detailed below.

### Third raid: 30-second check passed

- Local EventSub receipt: **16:51:46.120 +08:00**. The landing draft was created approximately
  **2 milliseconds** later using the already available transcript-based summary; this is server
  draft timing, not a measurement of video rendering.
- Twitch confirmed the manually approved chat message at **16:52:05.923 +08:00**:
  **19.803 seconds** after local EventSub receipt, including the wait for manual preview/confirmation.
  Message ID: `ffb45cd0-7a0d-4667-9af6-84afc9db643e`; draft status `sent`; no send error.
- The user explicitly confirmed seeing the guest card in B's **actual Twitch broadcast within
  30 seconds** of raid arrival. This is human observation, not frame-by-frame video timing.
- Audio capture remains active without reported errors, the summary is ready, and EventSub and
  Get Chatters remain connected. The updated longer HTML narration is represented in the live
  transcription and summary.
- At the 90-second cohort close, R = 0. The 60-second wave correctly reports insufficient
  samples with zero observed chat messages. The real five-minute checkpoint was observed at
  **16:56:49.253 +08:00**, 0.97 seconds after its scheduled time, with connected = 0,
  speakers = 0, follows = 0 and no error; cohort and chat completeness flags were true.
- The first raid also completed its real 15-minute sample without an error: R = 0, connected = 0,
  speakers = 0, follows = 0. The second raid has completed its five-minute sample with the same
  zero counts. These are empty-cohort checks; positive activity examples remain unverified.

### Closeout checks

- The first raid completed its actual **30-minute** checkpoint at **17:03:11.568 +08:00**,
  1.14 seconds after its scheduled time. R = 0, connected = 0, speakers = 0, follows = 0;
  no error, with cohort and chat completeness true. The real 5/15/30-minute empty-cohort
  observation paths have all been exercised.
- An allowlisted, aggregate-only [live evidence snapshot](evidence/live-run-2026-10-25.json)
  preserves observed timestamps, Twitch message references and actual samples. It excludes
  credentials, individual chatter IDs, raw chat, transcripts and audio.
- Closeout automated run: **50 tests passed**; Ruff, dependency-lock validation and the
  TypeScript/production build passed. The same upstream Starlette/httpx warning remains.
- A wheel unpacked outside the source tree imports its own package and serves the health,
  control room, overlay and Chinese guide routes successfully. The guide was initially absent
  from the wheel; it is now bundled with the OBS audio guide and third-party notices. The
  app-route checks were rerun after that packaging fix.

## Remaining live acceptance checks

| Boundary | Current status |
| --- | --- |
| Account A and B, broadcasting | User has both running; channel names confirmed by real raid events |
| Public Client DCF and EventSub against Twitch | Connected as B; three real raids received |
| OpenAI transcription/summary against the API | Succeeded with B's actual HTML audio |
| Actual A → B raid | Received three times; second and third raids have confirmed Twitch chat-send success |
| Overlay + chat within 30 seconds | Third raid: chat confirmed in 19.803 seconds from local receipt; user confirms overlay appeared in Twitch video within 30 seconds; video timing was not independently measured |
| Real 60-second wave learning | Insufficient-sample path observed; positive emote/token learning still pending |
| Actual five-minute observation | All three raids completed with empty cohorts and zero counts |
| Positive differential cohort, speech and follow examples | Requires actual new chat connections and real interactions |
| Actual 15/30-minute observations | First raid completed both with an empty cohort; valid zero counts and no sample errors |

No local unit test, mocked notification or setup-state screenshot is counted as completing a
live boundary. Remaining acceptance should use genuine new chat participants for positive
connection/speech examples and retain actual Twitch video/chat evidence for the submission.
