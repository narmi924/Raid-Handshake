"""Runtime deployment view. Build with the local paper-figures fig.ps1 runtime."""

from pathlib import Path

from paperfig import Figure, Theme, glyph, si

HERE = Path(__file__).parent
th = Theme.board(accent="#0E0E10", font="Inter").with_(
    ink="#0E0E10", ink_soft="#55555F", ink_faint="#666670",
    line="#55555F", group_fill="#FAFAFA", group_stroke="#C8C8CF",
    card_stroke="#ADADB8", dark_fill="#0E0E10", back="#55555F",
    radius_card=5, radius_group=8,
    sizes={"group": 21, "card": 19, "detail": 14.5, "label": 14.5, "small": 13},
)
f = Figure("architecture", th)

# Named rows and columns keep traffic on straight, distinct lanes.
LOCAL_X, LOCAL_Y, LOCAL_W, LOCAL_H = 330, 34, 520, 630
SERVICE_X, SERVICE_Y, SERVICE_W, SERVICE_H = 385, 270, 410, 150
SURFACE_Y, SURFACE_H = 120, 82
STUDIO_X, OBS_X, SURFACE_W = 350, 615, 210
STORE_Y, STORE_H = 570, 70
EVENT_Y, REQUEST_Y, RESULT_Y = 300, 382, 410

f.group(LOCAL_X, LOCAL_Y, LOCAL_W, LOCAL_H)
f.text(344, 44, 400, 32, f.t("B's Windows computer", role="group", weight=700))
f.text(344, 78, 400, 24, f.sub("127.0.0.1:8765 · no public callback"))
f.card(STUDIO_X, SURFACE_Y, SURFACE_W, SURFACE_H, "Studio browser", "Exact preview + confirm")
f.card(OBS_X, SURFACE_Y, SURFACE_W, SURFACE_H, "OBS overlay", "Read-only browser",
       icon=si("obsstudio"), isize=24)

# Actual project mark from frontend/src/studio.ts.
project_mark = glyph(
    '<path d="M7 12h17l-5-5M33 28H16l5 5M28 11l5 5-5 5M12 29l-5-5 5-5"/>',
    th.dark_ink, width=3, view=40,
)
f.card(SERVICE_X, SERVICE_Y, SERVICE_W, SERVICE_H, "Raid Handshake",
       "Context · signals · connection estimates", icon=project_mark, isize=30, tone="dark")
f.icon(770, 46, 19, si("fastapi"))
f.text(792, 43, 50, 24, f.sub("FastAPI", size=13))

audio_icon = glyph('<path d="M3 10v4m4-8v12m5-15v18m5-15v12m4-8v4"/>', th.ink)
f.card(640, 466, 185, 72, "Local audio", "Mic / system audio", icon=audio_icon, isize=22)
f.card(350, STORE_Y, 205, STORE_H, "OS keyring", "API key · Twitch tokens")
f.cylinder(575, STORE_Y, 250, STORE_H, "SQLite", "Raids · drafts · samples")

# One platform, two transports. No source-chat-history endpoint.
f.group(20, 204, 230, 266)
f.icon(37, 218, 28, si("twitch"))
f.text(78, 215, 150, 34, f.t("Twitch", role="group", weight=700))
f.card(35, 270, 200, 70, "EventSub", "Raid · chat · follows")
f.card(35, 362, 200, 78, "Helix", "Metadata · clips · chatters")
f.card(970, 300, 210, 130, "OpenAI API", "Transcription · summaries")

# External app traffic. EventSub uses an outbound WebSocket connection.
f.line([(235, EVENT_Y), (SERVICE_X, EVENT_Y)])
f.label(262, EVENT_Y - 11, 96, "Events")
f.line([(SERVICE_X, REQUEST_Y), (235, REQUEST_Y)])
f.label(254, REQUEST_Y - 11, 122, "Queries + chat")
f.line([(235, RESULT_Y), (SERVICE_X, RESULT_Y)], dashed=True)
f.label(265, RESULT_Y - 11, 94, "Results")
f.line([(SERVICE_X + SERVICE_W, 324), (970, 324)])
f.label(826, 313, 122, "Audio + text")
f.line([(970, 397), (SERVICE_X + SERVICE_W, 397)], dashed=True)
f.label(830, 386, 111, "AI results")

# Separate admin and read-only state, using local HTTP and WebSocket paths.
f.line([(430, SURFACE_Y + SURFACE_H), (430, SERVICE_Y)])
f.label(365, 225, 79, "Confirm", bg=th.group_fill)
f.line([(500, SERVICE_Y), (500, SURFACE_Y + SURFACE_H)])
f.label(474, 225, 65, "State", bg=th.group_fill)
f.line([(720, SERVICE_Y), (720, SURFACE_Y + SURFACE_H)])
f.label(688, 225, 65, "State", bg=th.group_fill)
f.line([(735, 466), (735, SERVICE_Y + SERVICE_H)])
f.label(746, 430, 65, "Speech", bg=th.group_fill)

# Arrowless dashed links indicate local persistence access, not external recipients.
f.line([(455, SERVICE_Y + SERVICE_H), (455, STORE_Y)], end=False, dashed=True, flow=None)
f.line([(600, SERVICE_Y + SERVICE_H), (600, STORE_Y)], end=False, dashed=True, flow=None)
f.text(350, 644, 475, 16, f.sub("Local persistence · credentials separate from runtime state", size=13))
f.text(20, 688, 400, 24, f.sub("Solid arrows: events / requests / state", size=14))
f.text(465, 688, 280, 24, f.sub("Dashed arrows: API results", size=14))
f.text(850, 688, 330, 24, f.sub("Dashed links: local persistence", size=14))

f.export(HERE / "architecture", formats=("png", "svg", "pdf"), motion=False)
