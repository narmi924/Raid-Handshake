from __future__ import annotations

import re
from collections import Counter, defaultdict

STOPWORDS = set(
    "the and for this that with from your you are was have has just what when where "
    "how not but can all our out its into they them then than here there it's i'm "
    "to of in is it on a an at as be we me my so do if or hi hey hello welcome raid".split()
)
TOKEN = re.compile(r"[^\W_][\w'-]{1,31}", re.UNICODE)


class WaveLearner:
    def __init__(self, source_id: str):
        self.source_id = source_id
        self.messages = 0
        self.authors: set[str] = set()
        self.emotes: Counter[str] = Counter()
        self.emote_users: dict[str, set[str]] = defaultdict(set)
        self.emote_meta: dict[str, dict] = {}
        self.tokens: Counter[str] = Counter()
        self.token_users: dict[str, set[str]] = defaultdict(set)

    def add(self, event: dict) -> None:
        user = event.get("chatter_user_id", "")
        if not user:
            return
        self.messages += 1
        self.authors.add(user)
        message = event.get("message", {})
        fragments = message.get("fragments", [])
        # Third-party emotes arrive as text; native emotes carry their actual owner_id.
        texts = []
        if not fragments:
            texts = [message.get("text", "")]
        for fragment in fragments:
            emote = fragment.get("emote") or {}
            if fragment.get("type") == "emote" and str(emote.get("owner_id")) == self.source_id:
                eid = str(emote.get("id", ""))
                if eid:
                    self.emotes[eid] += 1
                    self.emote_users[eid].add(user)
                    self.emote_meta[eid] = {
                        "id": eid,
                        "name": fragment.get("text", eid),
                        "owner_id": self.source_id,
                    }
            if fragment.get("type") == "text":
                texts.append(fragment.get("text", ""))
        for raw in TOKEN.findall(" ".join(texts)):
            token = raw.casefold()
            if token in STOPWORDS or token.isdigit() or raw.startswith("http"):
                continue
            self.tokens[token] += 1
            self.token_users[token].add(user)

    def result(self, final: bool = False) -> dict:
        enough = self.messages >= 3 and len(self.authors) >= 2
        emotes = (
            [
                dict(self.emote_meta[eid], count=count, users=len(self.emote_users[eid]))
                for eid, count in self.emotes.most_common(20)
                if count >= 3 and len(self.emote_users[eid]) >= 2
            ][:3]
            if enough
            else []
        )
        tokens = (
            [
                {
                    "text": token,
                    "count": count,
                    "users": len(self.token_users[token]),
                    "identity": "unverified text token",
                }
                for token, count in self.tokens.most_common(40)
                if count >= 3 and len(self.token_users[token]) >= 2
            ][:3]
            if enough
            else []
        )
        return {
            "status": ("learned" if emotes or tokens else "insufficient") if final else "learning",
            "messages": self.messages,
            "authors": len(self.authors),
            "emotes": emotes,
            "tokens": tokens,
            "scope": "Messages observed in the receiving channel during the first 60 seconds",
        }
