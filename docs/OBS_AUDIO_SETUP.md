# OBS and audio setup

Use the audio that channel B is actually broadcasting. You can use live microphone speech
or a spoken audio/video/HTML source; speaking into a separate microphone is not required.

## Microphone

1. In OBS, enable the microphone that supplies B's stream.
2. In Raid Handshake, open **Settings → Audio**, select that microphone and choose
   **Use this source**. In the studio, choose **Start listening**.
3. Wait for **Summary ready** before triggering a real raid. Keep listening enabled throughout
   the handoff. Expand **What your stream is doing** to inspect the summary and recent transcript.

## System audio: an HTML page, video or spoken recording

The simple route is the same playback device feeding two consumers:

- OBS Desktop Audio → Twitch B.
- Raid Handshake System audio → OpenAI transcription and summaries.

1. In Windows, select your intended speaker/headphone output. In OBS **Settings → Audio**,
   use that same device for **Desktop Audio**.
2. For the HTML Browser source, leave **Control audio via OBS** unchecked when using this
   Desktop Audio route. Keep Desktop Audio unmuted; mute **Mic/Aux** if you do not want to
   broadcast the physical microphone. Additional audio monitoring is unnecessary for this route.
3. Ensure the HTML speech is playing and OBS's Desktop Audio meter moves. If autoplay was
   blocked, right-click the Browser source → **Interact**, then click the page's audio control.
   A relative MP3 path must refer to an existing file beside the HTML page.
4. In Raid Handshake **Settings → Audio**, select **System audio** for the same playback
   device and choose **Use this source**. Choose **Start listening** in the studio.
5. Keep Twitch web players muted on the capture computer while leaving the intended Windows
   output and OBS Desktop Audio enabled. This prevents delayed stream audio being captured again.
6. Wait for the transcript and **Summary ready**. The summary should describe the audio actually
   being streamed. A repeated short phrase correctly produces only a short, limited summary.

The initial live tests used EDIFIER Halo Soundbar as both Windows output and OBS Desktop Audio,
with its corresponding System audio entry in Raid Handshake. Your own device name may differ.

## Keep the content source and overlay separate

The HTML/video is B's stream content. Raid Handshake is a second Browser source above it.
Open **Settings → Connections → Copy overlay URL**, add a new OBS Browser source, and set
its viewport to **1920 × 1080**. Keep **Local file** unchecked for this URL source. Fit it to
your canvas if needed. Do not replace the source that plays your content.

Twitch receives the audio OBS uploads; no additional Twitch webpage microphone selection is
required for B. Keep A's independent phone/computer broadcast running for the raid.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| OBS Desktop Audio meter does not move | Content playback, Windows output/volume and OBS device/mute state |
| OBS has audio but no transcript arrives | Matching System audio source, Start listening, then audio/API errors |
| Transcription works but summary is unavailable | Expand the context section; check model access/quota and refresh the summary |
| Repeated or delayed speech | Extra copies of the HTML player, unmuted Twitch web players, duplicate capture routes |
| Audio source changes while already listening | Use this source restarts active capture on the newly selected device |

After recording or testing is finished, **Pause** stops audio capture and new transcription
uploads. The Twitch connection and scheduled chat-connection observations can continue.

References: [OBS audio mixer](https://obsproject.com/kb/audio-mixer-guide),
[OBS browser source](https://obsproject.com/kb/browser-source).
