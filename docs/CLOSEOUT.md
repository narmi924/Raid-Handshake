# Release and submission checklist

Repository: **https://github.com/narmi924/Raid-Handshake**. This is the selected publication
destination. See the repository itself to confirm the latest pushed revision and CI status.

## Completed live evidence

- Genuine A `thisisraida` → B `thisisraidb` raids, with B on OBS and A on a phone.
- Actual OpenAI transcription and summaries from B's broadcast audio.
- A manually approved Twitch message confirmed **19.803 seconds after local EventSub receipt**.
- Broadcaster confirmation that the guest card appeared in B's actual Twitch broadcast within
  thirty seconds. This is human observation, not independent frame-by-frame timing.
- Real five-, fifteen- and thirty-minute observations with an empty estimated cohort and no
  sample errors. [Evidence and limits](VERIFICATION.md) remain explicit.

The interface has since been simplified to guided setup, a focused studio and a Settings
dialog using [the supplied Twitch design reference](twitch.design.md). The earlier live
timing belongs to the earlier interface; run a final real take with the redesigned interface.

## Remaining user actions

1. **Final real take.** Start listening, wait for Summary ready, then run the genuine raid.
   Review and send the exact welcome text. Confirm the overlay and Twitch chat in the recording.
2. **Positive interaction example.** If available, use genuine participants who are in A's
   chat before arrival and not already connected to B. They should connect to B within the
   ninety-second arrival window and send ordinary messages. Keep actual counts, including zeros.
   Positive-cohort, positive speech/follow and positive wave-learning examples are not yet verified.
3. **Video.** Preserve continuous footage from before the raid through its five-minute sample,
   then edit a clearly labeled time jump. Include actual Codex footage. Follow the
   [2:45 English recording script](DEMO_SCRIPT.md), upload to YouTube with **Public** visibility,
   and check the link while signed out.
4. **Submit.** Review the English description, repository access, video link, team information
   and session ID in Devpost, then submit before the cutoff.

## English submission materials

| Item | File / value |
| --- | --- |
| Project description and Codex usage | [SUBMISSION.md](SUBMISSION.md) |
| Installation and judging instructions | [JUDGE_GUIDE.md](JUDGE_GUIDE.md) |
| OBS/audio walkthrough | [OBS_AUDIO_SETUP.md](OBS_AUDIO_SETUP.md) |
| Real demo capture/edit script | [DEMO_SCRIPT.md](DEMO_SCRIPT.md) |
| Test and real-service evidence | [VERIFICATION.md](VERIFICATION.md) |
| Codex build session | `01a17154-fef0-76f1-b2bb-cb54cdf374ae` |
| Deadline | **November 3, 2026, 06:00 Singapore**, equivalent to November 2, 14:00 Pacific |

Use the default exact-preview/manual-send path for the recorded take. Optional template auto
mode is implemented and tested locally, but no real automatic-publishing run is claimed.
The README documents third-party processing and publishing terms questions without claiming
a blanket sponsor waiver. Use authorized audio, imagery and participant footage.

The local source package excludes `.env`, runtime databases, credentials, raw chat/transcripts,
test MP3s, `tmp/`, and recording originals. The optional Chinese setup notes have English
counterparts above; the interface and primary submission materials are English.

Requirements: [official hackathon rules](https://twitchcon-codex.devpost.com/rules).
