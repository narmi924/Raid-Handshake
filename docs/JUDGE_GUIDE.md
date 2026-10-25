# Raid Handshake — judge run and test guide

## What you need

- A Windows 10/11 computer with OBS Studio and [uv](https://docs.astral.sh/uv/getting-started/installation/).
  uv can provision Python 3.11. Node.js 24 is only required when rebuilding the supplied frontend.
- Two Twitch accounts/channels, A and B, capable of broadcasting at the same time; a phone
  for A plus the Windows computer for B is sufficient.
- A Twitch application registered as a **Public Client**, and its Client ID. Authorize as B.
- An OpenAI API project/key with billing, quota and access to the configured models. The app
  supplies no shared API credentials. Default models are `gpt-transcribe` and `gpt-4.1-mini`.
- Authorized audio and actual Twitch participants. An independent participant is useful for
  a positive new-connection cohort; no simulated raid route is provided.

The current live test accounts are `thisisraida` and `thisisraidb`. Their passwords, stream keys
and OAuth/API credentials are not distributed. You may use your own A/B accounts.

## Install and run

From an extracted source archive or a repository checkout, in PowerShell:

```powershell
uv sync --python 3.11 --frozen
uv run raid-handshake
```

Open **http://127.0.0.1:8765**. The source distribution includes the built interface. To
rebuild it from TypeScript:

```powershell
npm ci
npm run build
```

The service binds to localhost and needs no public webhook, HTTPS tunnel or Twitch Extension
review. Global Ctrl+Shift+Enter requires Windows; the on-screen send button is also available.

## Connect and prepare

1. In setup step 1, enter the Public Client ID, select **Connect Twitch**, and
   complete Twitch's official Device Code authorization **as B**. The receiving channel name
   must match B. No Client Secret or separate bot account is needed.
2. In setup step 2, add your OpenAI key locally. It is never returned in the state response.
3. Choose the authorized microphone, or the matching speaker entry marked **System audio**
   for speech actually being broadcast from a local player. Select **Start listening**. Maintain
   real speech until **Recent transcript** is populated and **Summary ready** appears.
4. If using system playback, mute Twitch web players on the capture computer to avoid feeding
   delayed stream audio back into capture. Keep the intended audio output and OBS input enabled.
5. Open **Settings → Welcome** to set actual participation hints, one rule and language. Save welcome settings. Leave the
   optional automatic template mode off for the default exact-preview test.
6. In setup step 3, select **Copy overlay URL** and add it as a separate **1920×1080 Browser source**, above B's
   content. Open the studio after adding it. The link is also in **Settings → Connections**.
   Keep its read-only key private. It is distinct from any HTML content source.
7. Start A and B broadcasts. Allow incoming raids from A in B's channel settings. Wait for the
   studio to show **Ready for a raid**. Detailed connection state is under **Settings → Advanced**.

New channels can correctly show no clips and insufficient source-emote samples. These do not
prevent testing the real event, transcript, welcome card or observation schedule.

## Run the real test

1. A genuine participant should be in A's chat before the raid and not already connected to B.
   Existing B chat connections form the baseline and do not become new arrivals.
2. In A's Twitch chat, issue `/raid B_LOGIN`, replacing B_LOGIN with the actual receiving login.
   Complete Twitch's countdown/confirmation. Keep B and the local service running.
3. Verify the guest card in B's actual Twitch video, including source/title/category and
   reported raid size. The source lookup budget is 4.5 seconds; unavailable fields are labeled.
4. In the studio, read the complete generated welcome, then select **Send welcome message**
   or press **Ctrl+Shift+Enter**. Verify the real message in B's Twitch chat.
5. Record the native Twitch raid arrival and when the overlay and chat message become visible.
   Local receipt-to-send timing is useful evidence but is not identical to video display timing.
6. During the first sixty seconds, participants may send ordinary real chat and familiar
   emotes. Learning requires at least three occurrences and two authors; sparse samples are
   labeled insufficient. Third-party text is not claimed as verified native emote ownership.
7. Keep participants connected to B. The estimated cohort closes ninety seconds after arrival.
   Expand **After the hello**. At five, fifteen and thirty minutes, inspect actual observation timestamps and counts.
   A cohort member must send an ordinary message within the preceding five minutes to count
   as a recent speaker. Follow counts cover the whole channel since the raid, not only the cohort.

## Interpret results

The app compares chat connections, not video viewers. R is the union of accounts newly observed
within ninety seconds relative to the pre-raid baseline; platform update delays and unrelated
arrivals affect it. A report of R = 0 is a valid empty-cohort observation, not proof that a raid
had no viewers. A failed/missed observation is unknown rather than a manufactured zero.

Do not restart the service during a timed run: missing chat/follow intervals are marked
incomplete, and a restart does not reconstruct events it never observed.

## Current evidence and limitations

The [verification record](VERIFICATION.md) distinguishes automated checks, actual Twitch/OpenAI
results, the 19.803-second chat send, the broadcaster's overlay timing confirmation, and checks
still pending. It contains no shared credentials. Test fixture events are not demo footage.

The default publishing path previews exact text. Optional template mode sends varying text
without a new per-card confirmation. Cloud processing and dynamic publishing retain the terms
questions documented in the README; no blanket sponsor exception is claimed.

## Development checks

```powershell
uv sync --python 3.11 --extra dev --frozen
uv run pytest -q
uv run ruff check src tests
npm ci
npm run build
```

These tests use isolated credentials and HTTP stubs, not live Twitch events or the judge's key.
