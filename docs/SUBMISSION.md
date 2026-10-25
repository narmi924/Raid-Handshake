# Raid Handshake — submission description

Copy-ready English project description. Add the final repository and public YouTube links
to the submission form after publication; neither has been published by this preparation step.

## Project name

Raid Handshake

## Tagline

A live handoff for Twitch raids: source context for streamers, transcript-grounded welcome
cards for arrivals, and honest estimates of new chat connections.

## Inspiration

A raid brings a community into another stream, but the conversation it came from rarely
arrives with it. The receiving streamer knows who sent the raid and how many people Twitch
reported. New arrivals still have to work out what is happening, how to participate, and what
the channel expects. The first welcome deserves more context than a generic thank-you.

Raid Handshake focuses on that handoff. It complements native raids and shoutouts with
current content context in both directions.

## What it does

For the receiving streamer, an OBS browser overlay shows the real source channel, reported
raid size, current or last available title/category, and up to three available recent clip
titles. During the first 60 seconds it learns source-owned native emotes and repeated text
from the receiving chat. Sparse samples are labeled insufficient rather than invented.

For arriving viewers, a short chat card explains the receiving stream's current activity,
actual participation hints and one channel rule. OpenAI transcribes authorized live audio
and generates a rolling, transcript-grounded summary. The streamer previews the complete
card and confirms it with a button or global hotkey. An optional, initially disabled mode
can fill and send a broadcaster-approved template automatically.

After the raid, cards at five, fifteen and thirty minutes report estimates of new chat
connections and recent speakers, plus whole-channel follow events. These are chat-connection
observations, not video-viewing retention or a verified list of raid members.

## How it was built

The app runs locally on Windows with a FastAPI service, a TypeScript/Vite control room,
SQLite session state and a transparent OBS browser source. Twitch Public Client Device
Code Flow connects the receiving broadcaster. EventSub WebSocket supplies real raid,
chat and follow events, while paginated Get Chatters snapshots support the connection estimate.

OpenAI API transcription processes short voiced audio segments. Structured Responses summaries
must cite excerpts that actually exist in the spoken transcript. There is no silent
title/category-only fallback when audio is missing. Credentials use the operating system
credential manager where available, with an explicitly labeled session-memory fallback.

## How Codex was used

Codex helped audit Twitch's API capabilities, turn the user stories into the local app,
implement OAuth and EventSub, integrate transcription and structured summaries, build the
control room and overlay, and check the cohort and send-state logic. We iterated in this
build thread against two real Twitch channels. Codex also created setup documentation,
automated checks and the submission preparation documents.

The developer performed account setup, broadcaster authorization, the real broadcasts,
raids and manual publishing confirmations. These live steps were not replaced with fixtures.

Codex build session ID: **01a17154-fef0-76f1-b2bb-cb54cdf374ae**.

## Challenges and decisions

Twitch does not expose a list identifying the individuals who arrived with a raid. We use
a pre-raid chatters snapshot and the union of new chat connections during the next ninety
seconds, and display the method and update-delay caveat. Unrelated arrivals can enter that
estimate. Missing observations remain unknown; they are not converted into zeros.

We also kept publishing under broadcaster control. The default path previews the exact
message, prevents duplicate sends, and does not retry when delivery is uncertain. Optional
template approval is clearly distinguished from previewing each dynamically generated message.

## What we verified

On October 25, 2026, an actual `thisisraida` → `thisisraidb` raid generated a landing draft
from an already warm audio summary. Twitch confirmed the manually approved chat message
**19.803 seconds after the app received EventSub**. The broadcaster confirmed the guest
card appeared in the actual Twitch broadcast within thirty seconds. The video timing was
human-observed, not independently measured frame by frame.

Real five-, fifteen- and thirty-minute samples completed with an empty new-connection cohort. That
verifies the timed observation path for zero arrivals; it does not establish improved viewer
retention. Positive-cohort examples remain unverified; see the
[current verification record](VERIFICATION.md). Update this paragraph only after additional
real evidence exists.

## What's next

Finish a small live test with genuine new chat participants, document the full observation
window, and gather streamer feedback on whether the handoff card makes welcoming easier.
We would evaluate that benefit directly before making any claim about retention uplift.

## Links and submission fields

- Repository URL: not published yet; enter the final accessible repository URL.
- Demo URL: not recorded/uploaded yet; enter the final publicly visible YouTube URL.
- Platform: Windows 10/11; local browser control room and OBS Studio browser source.
- Testing instructions: [English judge guide](JUDGE_GUIDE.md).
- Codex session ID: `01a17154-fef0-76f1-b2bb-cb54cdf374ae`.

The final entry needs accessible source, an English description/testing instructions, a
public YouTube demonstration under three minutes showing Twitch and Codex, and the session
ID. Check the [official requirements](https://twitchcon-codex.devpost.com/rules) before submitting.
