# Raid Handshake — accepted implementation scope

The first milestone is a genuine A → B Twitch raid. Tasks take priority over calendar dates.

## Current decisions

- Windows local service: Python/FastAPI, TypeScript/Vite control room and OBS browser source.
- Public Client Device Code Flow; broadcaster user token; EventSub WebSocket.
- OpenAI API for both transcription and summaries. No faster-whisper, Ollama, or local model runtime.
- Microphone / authorized audio device capture is explicit; rolling three-minute transcript.
- US1: immediately show real channel metadata and available clips. After 60 seconds, enrich the card with source-owned native emotes and repeated text tokens observed in B. Third-party emote identity is not claimed. Show insufficient samples explicitly.
- US3: record the freshest pre-raid chatter snapshot S0, union new accounts observed in the next 90 seconds into R, and sample R ∩ current chatters at 5/15/30 minutes. Message counts cover the preceding five minutes. Count channel.follow events separately for the entire window.
- R is an estimate of new chat connections following a raid; it is not a verified list of raiders or viewers. Baseline freshness, missed polls and overlapping windows are visible.
- Default sending is exact-text preview + global hotkey. Optional preapproved-template mode fills a changing current summary and sends automatically; it starts disabled and is enabled by the broadcaster.
- No self-report command or enrollment window.

## Work order

1. [x] Account/channel setup guide, application configuration and credential storage.
2. [x] Implement device login, EventSub subscriptions, connection health, chat send and OBS rendering.
3. [x] Implement OpenAI transcription/summary, preview/hotkey and preapproved template modes.
4. [x] Implement chatter polling/differential cohorts, follow counts and 60-second wave learning.
5. [x] Local automated checks and disconnected-state browser checks.
6. [x] User prepares A/B accounts, broadcasts, Public Client ID and OpenAI API key.
7. [x] Verify Twitch authorization, OpenAI processing and the first genuine A → B raid.
8. [x] Timed real raid: chat sent within 30 seconds; user confirms the overlay appeared in the
   actual Twitch broadcast within 30 seconds.
9. [x] Observe actual five-, fifteen- and thirty-minute checkpoints with an empty cohort.
10. [x] Prepare English project description, judge guide, recording script, session ID and
    sanitized live evidence; check packaging and source hygiene.
11. [ ] Verify positive chat-connection/speech examples with genuine new participants.
12. [ ] Record and publicly upload the real demo; publish an accessible repository; submit Devpost.

The first live connection milestone is achieved. On 2026-10-25 three genuine incoming raids
from `thisisraida` to `thisisraidb` were received. On the third raid, Twitch confirmed the
manually approved landing card **19.803 seconds** after local EventSub receipt, with OpenAI
audio processing already running. The user confirmed seeing the overlay in the actual Twitch
broadcast within 30 seconds. Real five-, fifteen- and thirty-minute samples have completed with
empty cohorts. Positive-cohort examples and recorded submission evidence
remain open; see [verification](docs/VERIFICATION.md).

## External dependencies

Accounts, dual broadcasts, B authorization and the OpenAI API key are configured. Another timed
raid needs continuously running authorized audio, a fresh summary before arrival, and genuine
participants for a positive differential cohort. Code or fixtures do not satisfy live acceptance.

## Terms and data handling

The user's selected implementation uses cloud OpenAI processing and optional dynamic auto-publishing. Sponsorship does not by itself establish the written sharing authorization described by Twitch Developer Services Agreement VI.C. Approval of a template's structure does not establish that the eventual generated text was previewed. These are documented open interpretation/authorization questions, not claims of official approval. Implementation proceeds as requested; automatic mode is off by default.

Audio is buffered in memory. Transcript/chat context has a bounded lifetime. API keys and OAuth tokens are held in the OS credential store where available, with session-memory fallback explicitly reported. No transcript or audio is committed or included in diagnostic logs. OpenAI Responses use store=false, which is not a promise of zero provider retention.

## Acceptance evidence

- Real incoming raid, not a CLI/simulated notification.
- Guest card and chat message visible on Twitch within 30 seconds, measured from the native raid notification and including stream delay.
- Wave enrichment at 60 seconds with samples / insufficient-sample state.
- Actual 5-minute chatter snapshot with the method and delay caveat displayed.
- 15/30-minute paths verified with real elapsed time; missed observations reported as unknown.
