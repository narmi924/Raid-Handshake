from raid_handshake.learning import WaveLearner


def message(user, text="", fragments=None):
    return {
        "chatter_user_id": user,
        "message": {
            "text": text,
            "fragments": fragments if fragments is not None else [{"type": "text", "text": text}],
        },
    }


def emote(owner, name="SourceHype", identity="emote-1"):
    return {"type": "emote", "text": name, "emote": {"id": identity, "owner_id": owner}}


def test_only_source_owned_native_emotes_are_learned():
    learner = WaveLearner("source")
    for user in ("one", "two", "one"):
        learner.add(message(user, fragments=[emote("source"), emote("other", "Other", "other-id")]))
    result = learner.result(final=True)
    assert result["emotes"] == [
        {"id": "emote-1", "name": "SourceHype", "owner_id": "source", "count": 3, "users": 2}
    ]


def test_third_party_emote_like_text_remains_unverified_text():
    learner = WaveLearner("source")
    for user in ("one", "two", "three"):
        learner.add(message(user, "OMEGALUL the and"))
    result = learner.result(final=True)
    assert result["emotes"] == []
    assert result["tokens"] == [
        {"text": "omegalul", "count": 3, "users": 3, "identity": "unverified text token"}
    ]


def test_one_person_spamming_does_not_establish_a_community_signal():
    learner = WaveLearner("source")
    for _ in range(20):
        learner.add(message("one", "party party party", [emote("source")]))
    result = learner.result(final=True)
    assert result["status"] == "insufficient"
    assert not result["emotes"] and not result["tokens"]


def test_unicode_catchphrases_are_supported():
    learner = WaveLearner("source")
    for user in ("a", "b", "c"):
        learner.add(message(user, "冲鸭"))
    assert learner.result(final=True)["tokens"][0]["text"] == "冲鸭"


def test_empty_wave_reports_insufficient_not_an_invented_phrase():
    result = WaveLearner("source").result(final=True)
    assert result["status"] == "insufficient"
    assert result["messages"] == 0
