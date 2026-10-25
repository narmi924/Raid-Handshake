"""Default exact-preview raid sequence; vertical spacing is schematic."""

from pathlib import Path

from paperfig import Figure, Theme, glyph, si

HERE = Path(__file__).parent
th = Theme.board(accent="#0E0E10", font="Inter").with_(
    ink="#0E0E10", ink_soft="#55555F", ink_faint="#666670", line="#55555F",
    group_fill="#FAFAFA", group_stroke="#C8C8CF", card_stroke="#ADADB8",
    dark_fill="#0E0E10", back="#55555F", radius_card=5, radius_group=0,
    sizes={"group": 20, "card": 19, "detail": 15.5, "label": 16, "small": 14},
)
f = Figure("raid-sequence", th)

X = {"twitch": 125, "service": 390, "ai": 655, "studio": 920, "obs": 1185}
HEADER_Y, HEADER_H, HEADER_W = 30, 62, 185
LIFE_TOP, LIFE_BOTTOM = HEADER_Y + HEADER_H, 1170
ROWS = {
    "audio": 160, "transcript": 194, "context": 228, "summary": 262,
    "baseline_request": 300, "baseline_result": 334,
    "raid": 400, "facts": 434,
    "lookup": 504, "draft": 504, "metadata": 542, "enriched": 584,
    "preview": 665, "confirm": 700, "send": 735, "sent": 770, "welcome": 805,
    "chat": 885, "wave": 920, "arrival_poll": 960, "arrivals": 994,
    "checkpoint_poll": 1040, "checkpoint_result": 1075, "sample": 1110,
}

project_mark = glyph(
    '<path d="M7 12h17l-5-5M33 28H16l5 5M28 11l5 5-5 5M12 29l-5-5 5-5"/>',
    th.dark_ink, width=3, view=40,
)
for name, title, icon in (
    ("twitch", "Twitch", si("twitch")),
    ("service", "Local service", project_mark),
    ("ai", "OpenAI API", None),
    ("studio", "Studio", None),
    ("obs", "OBS overlay", si("obsstudio")),
):
    x = X[name]
    f.card(x - HEADER_W / 2, HEADER_Y, HEADER_W, HEADER_H, title, icon=icon,
           tone="dark" if name == "service" else "card", isize=22)
    # A narrow dashed native shape is both a visible lifeline and the message anchor.
    # Lifeline crossings are intentional in a sequence, not component-box crossings.
    f.box(x - 0.5, LIFE_TOP, 1, LIFE_BOTTOM - LIFE_TOP,
          fill="none", stroke=th.group_stroke, r=0, width=0.8,
          extra="dashed=1;dashPattern=5 4;", role="shape", check=False)


def phase(y, title):
    f.box(27, y, 1250, 30, fill=th.canvas, stroke="none", r=0, role="band", check=False)
    f.text(35, y, 1235, 30, f.t(title, role="detail", weight=700))


def message(source, target, row, title, response=False, label_at=None):
    a, b = X[source], X[target]
    direction = 1 if b > a else -1
    y = ROWS[row]
    f.line([(a + direction * 0.5, y), (b - direction * 0.5, y)], dashed=response)
    left, width = min(a, b) + 15, abs(b - a) - 30
    if label_at is not None:
        left, width = label_at
    f.label(left, y - 13, width, title)


phase(104, "Before the raid · independent background tasks")
message("service", "ai", "audio", "Voiced audio")
message("ai", "service", "transcript", "Transcript", response=True)
message("service", "ai", "context", "Transcript + chat")
message("ai", "service", "summary", "Summary + evidence", response=True)
message("service", "twitch", "baseline_request", "Chatters poll")
message("twitch", "service", "baseline_result", "Complete snapshot S0", response=True)

phase(342, "Incoming raid · default manual-send mode")
message("twitch", "service", "raid", "channel.raid")
message("service", "obs", "facts", "Initial guest facts", label_at=(790, 340))

# UML-style parallel frame: neither preparation branch waits for the other.
f.box(33, 460, 1244, 152, fill="none", stroke=th.card_stroke, r=0, role="group", check=False)
f.box(33, 460, 63, 26, fill=th.group_fill, stroke=th.card_stroke, r=0, role="tab", check=False)
f.box(97, 461, 1179, 24, fill=th.canvas, stroke="none", r=0, role="band", check=False)
f.text(44, 460, 45, 26, f.t("par", role="detail", weight=700))
f.text(115, 460, 1135, 26, f.sub("Guest enrichment and welcome preparation run independently."))
message("service", "twitch", "lookup", "Source lookups")
message("twitch", "service", "metadata", "Metadata + clips", response=True)
message("service", "obs", "enriched", "Enriched guest card", label_at=(790, 340))
message("service", "studio", "draft", "Cached-summary draft")
f.box(410, 620, 790, 28, fill=th.canvas, stroke="none", r=0, role="note", check=False)
f.text(410, 620, 790, 28, f.sub("A fresh transcript is required; without it the welcome draft stays blocked."))

message("studio", "service", "preview", "Preview exact text")
message("studio", "service", "confirm", "Confirm send")
message("service", "twitch", "send", "Send message")
message("twitch", "service", "sent", "Message ID", response=True)
message("service", "obs", "welcome", "Sent welcome", label_at=(790, 340))

phase(830, "Observation windows · start at raid, independent of send")
message("twitch", "service", "chat", "B chat + follows")
message("service", "obs", "wave", "Community signals · first 60 s", label_at=(740, 420))
message("service", "twitch", "arrival_poll", "Polls · first 90 s")
message("twitch", "service", "arrivals", "Arrival snapshots", response=True)
f.box(415, 980, 735, 28, fill=th.canvas, stroke="none", r=0, role="note", check=False)
f.text(415, 980, 735, 28, f.sub("R = union of new connections relative to S0"))
message("service", "twitch", "checkpoint_poll", "Polls · 5 / 15 / 30 min")
message("twitch", "service", "checkpoint_result", "Complete snapshot", response=True)
message("service", "obs", "sample", "Connections · speakers · follows*", label_at=(735, 435))
f.box(27, 1136, 1250, 28, fill=th.canvas, stroke="none", r=0, role="note", check=False)
f.text(35, 1136, 1240, 28, f.sub("* Follows cover the whole channel. Connections estimate arrivals, not verified raiders or video viewers."))
f.text(35, 1184, 1240, 28, f.sub("Solid: requests / events / state   ·   Dashed: responses   ·   Vertical spacing is not to scale"))

f.export(HERE / "raid-sequence", formats=("png", "svg", "pdf"), motion=False)
