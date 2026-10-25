# Raid Handshake — real demo recording script

**Target edit: 2:45, English.** Record the real run first; record narration afterwards.
You do not need to speak live or enable a physical microphone. This is a filming script,
not a claim that the final video has been recorded or uploaded.

The [official rules](https://twitchcon-codex.devpost.com/rules) ask for a video under three
minutes, footage of the project functioning on Twitch and being built with Codex, and a
publicly visible YouTube upload. Keep submission materials in English. Checked October 25, 2026.

## 1. Prepare the actual take

| Item | Set it before recording |
| --- | --- |
| Source A | Phone broadcasting as **thisisraida**. Keep a separate A-signed-in chat/dashboard available to start the raid; B's browser stays signed in as B. |
| Receiving B | OBS broadcasting as **thisisraidb**, with the actual content source and Raid Handshake overlay as two separate sources. |
| Broadcast audio | Play your owned/authorized spoken HTML or media content. Windows output, OBS **Desktop Audio** and Raid Handshake **System audio** must use the same device. Mute OBS **Mic/Aux** if you do not want to speak. Keep Twitch web players muted on this computer. See [audio setup](OBS_AUDIO_SETUP.md). |
| Local studio | Open **http://127.0.0.1:8765**, choose **Start listening**, and wait for **Summary ready**. Expand **What your stream is doing** and check the transcript/evidence describe the audible content. |
| Welcome settings | In **Settings → Welcome**, use English, a real participation hint and one rule. Keep **Automatic sending: Off**. Close Settings before the raid so the full message can be previewed. |
| Baseline | In **Settings → Advanced → Connection diagnostics**, check Twitch/EventSub and Chatters are connected, with a fresh baseline. Wait for several successful polls before starting the raid. Close Settings again. |
| Participants | If available, invite genuine participants to watch A before the raid and follow Twitch's raid to B. They should not already have B's chat open. Preserve actual zeros or unknowns; a positive count is not a recording prerequisite. |
| Capture | Record the desktop so the studio and B's actual Twitch player/chat are readable. OBS's **Start Recording** captures its scene; by itself it does not capture the separate local-studio window. A parallel OBS scene recording is useful as a clean stream copy. |

Use a 1920 × 1080 desktop recording at 30 fps or higher. Enlarge browser text enough to read
an entire welcome. Keep the clock visible. Put the studio and B's Twitch player/chat side by
side; use a separate browser profile/device for A. Keep credentials, activation codes, stream
settings and the private overlay URL out of the recording.

Use a descriptive spoken segment rather than only “Hi, this is Raid B test.” Prerecorded
speech is valid input to this test when it is actually broadcast; describe it as such.
Do not route this video's later voiceover into B's stream or the app's audio capture.

## 2. Record one continuous live run

Start recording **at least 30 seconds before** initiating the raid and continue until the
real five-minute observation appears, ideally through T+6:00. Here **T0 means the incoming
raid**, not the beginning of the edited video.

| Real-run point | What you do | Evidence to keep |
| --- | --- | --- |
| Before T0 | Show A and B live, then B's actual content and **Summary ready**. Briefly open the context section, then close it. | Channel names/live indicators, transcript and supporting excerpt. |
| Start the raid | In A's chat, send **`/raid thisisraidb`**, then follow Twitch's actual countdown/confirmation. Keep B broadcasting. | Native Twitch raid action and actual arrival; no injected event or simulated button. |
| T0 → first card | Keep B's real Twitch player and studio in frame. | Source identity/raid size, title/category and available clips. “No recent clips” is valid. Retain the Twitch player's real broadcast delay. |
| Draft arrives | Read the entire welcome; click **Send welcome message** once, or press **Ctrl+Shift+Enter** after previewing it. | Exact text before confirmation, the action, **Delivered to Twitch chat**, and the same text in B's actual chat. Keep this segment at normal speed and unbroken. |
| First 60 seconds | Let genuine chat happen. Participants may converse normally about the stream. | **Community signals** after the learning window. Preserve **Not enough samples from different people yet** when that is the result. |
| First 90 seconds | Keep the app and Twitch connection running; do not switch receiving accounts or restart. | The actual arrival window and cohort, including zero. Do not open B's chat as test users just to manufacture an arrival. |
| T+5:00 onward | Expand **After the hello**; wait for the **5m** row's **Observed** time. Also capture the card in B's Twitch player if visible. | Connected, Spoke in last 5m, Follows*, observation time and caveats. Keep unknowns as unknowns. |
| After the sample | Stop recording and save the continuous original. **Pause** listening when finished. | Raw footage from pre-raid through the five-minute result. The short demo does not need a 15/30-minute wait. |

If a fresh summary is unavailable or the send fails, keep that take for debugging and record
another genuine raid once fixed. Do not patch an earlier card/chat result into a different
take. Avoid overlapping raid windows when recording a clean example.

The new take establishes its own timing. The earlier **19.803 s** result belongs to a previous
test and earlier UI; do not put it on new footage. Any timer must state its origin, for example
**“Since local EventSub receipt”**. A Twitch-player arrival is a different clock because the
broadcast is delayed. Do not combine those measurements.

## 3. Record actual Codex footage separately

Capture 20–30 seconds in this project's real Codex thread. Show a relevant request, actual
work/diff, then readable source or test results. Useful subjects are EventSub, transcript
grounding, complete Chatters pagination and duplicate-send handling. Scroll through material
that really exists; do not stage a generated conversation.

For fresh test-output footage, run **`uv run pytest -q`** in the repository and capture its
actual final result. Use whatever count/result it reports. Keep tokens, `.env`, credential
files, raw user messages and unrelated private tabs out of frame. Include the session ID in
the end card; showing the full conversation history is unnecessary.

## 4. Edit to 2:45

The table uses **final-video time**, not the raid clock. Rehearse the real send before choosing
edit points. Preserve arrival → preview → confirm → chat at normal speed; allow up to **2:55**
if the real section needs longer. Never speed it up to imply a faster handoff.
You may shorten Twitch's pre-arrival countdown with a clear **“Raid countdown omitted”**
caption; the continuous critical segment starts at the actual incoming raid.

| Video time | Picture and edit | English voiceover, ready to read |
| --- | --- | --- |
| **0:00–0:12** | A and B genuinely live. Small title: **Raid Handshake**. | “A raid moves a community in seconds, but leaves context behind. Raid Handshake helps both sides understand each other before the first hello is over.” |
| **0:12–0:28** | B's actual audio/content, transcript, evidence and **Summary ready**. | “This is channel B's actual broadcast. OpenAI transcribes its audio and keeps a short summary ready. The welcome uses that spoken context, with chat as supporting material.” |
| **0:28–1:06** | A's raid action, native arrival, guest card in actual B video, full draft, one confirmation and real chat delivery. Keep the critical sequence continuous. | “Now channel A sends a real raid to B. The streamer gets the source channel, raid size and available clip context. New arrivals get an introduction to B's current stream, a way to join in and one rule. I review this exact message, confirm once, and here it is in Twitch chat.” |
| **1:06–1:19** | First-minute **Community signals**. If cutting ahead, caption **Real run · +60 seconds**. | “During the first minute, the app learns source-owned emotes and repeated phrases from B's chat. A quiet room stays labelled as insufficient samples.” |
| **1:19–1:41** | Caption **Same real run · 5 minutes later · waiting interval omitted**, then actual **5m** row and observation time. Hold the numbers. | “Five minutes later, these are the real observations. The cohort estimates newly connected chat accounts. It reports who is still connected and who spoke recently. Follows cover the whole channel. These are chat connections, not video-viewing retention.” |
| **1:41–2:09** | Actual Codex thread → actual implementation diff/source → actual test output. | “I built this with Codex, from checking Twitch's API limits to implementing login, EventSub and the OBS overlay. Codex also helped ground summaries in transcript evidence and check pagination, missed observations and duplicate sends. The final validation uses real Twitch channels.” |
| **2:09–2:28** | Real studio and B's player/chat together. Optional Settings shot only if time remains. | “The daily flow is small: start listening, review one welcome and send. One local service and one OBS browser source connect the handoff, while missing data stays visible instead of becoming a made-up result.” |
| **2:28–2:45** | Real result behind the end card. Hold repository link and session ID. | “Raid Handshake: a better first hello between communities. The repository includes setup instructions, the architecture and the limits of the measurements. Built with Codex.” |

Do not read the sample's numbers before you have the take. Optionally add a short sentence
reporting the **actual** sample, such as “This run observed zero estimated new connections.”
Use that only if the visible result is zero. If the result is unknown, say so and retain the
reason; never convert it to zero.

Record narration after the run, or use an English voice you are authorized to use. Your live
Twitch microphone can stay muted. Add readable English subtitles and leave space around the
native raid notice, full welcome text and metric labels.

## 5. End card and publication

Use this closing text:

```text
Raid Handshake
Context for both sides of a Twitch raid

github.com/narmi924/Raid-Handshake
Built with OpenAI Codex
Session: 01a17154-fef0-76f1-b2bb-cb54cdf374ae

Real Twitch raid · OpenAI transcription · OBS overlay
Chat-connection estimates, not viewing retention
```

Before publishing:

- Export **1920 × 1080**, English captions, duration **less than 3:00**.
- Include real Twitch operation **and** real Codex build footage, not just terminal tests.
- Keep the continuous original; label the five-minute cut explicitly.
- Check that keys, OAuth/activation codes and the private overlay URL never appear.
- Use owned/authorized content and voice; skip background music unless you have the rights.
- Upload to **YouTube → Public**, test signed out, then add that URL to Devpost and
  [SUBMISSION.md](SUBMISSION.md). A local MP4 or private link is not the submitted demo.

Suggested title: **Raid Handshake — Real Twitch Raid Demo | Codex x TwitchCon 2026**.

Suggested YouTube description:

```text
Raid Handshake carries live context across a real Twitch raid.
This demo shows thisisraida → thisisraidb, an OBS guest card, a transcript-grounded
welcome approved by the broadcaster, and an actual five-minute chat-connection sample.
The waiting interval is clearly cut; chat connections are not video-viewing retention.

Source and setup: https://github.com/narmi924/Raid-Handshake
Built with OpenAI Codex.
Codex session: 01a17154-fef0-76f1-b2bb-cb54cdf374ae
```
