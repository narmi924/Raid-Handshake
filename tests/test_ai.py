import io
import time
import wave
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
import pytest

from raid_handshake.ai import Context, OpenAIContext, SummaryContent
from raid_handshake.audio import pcm_wav
from raid_handshake.config import ChannelConfig


def test_audio_is_a_valid_mono_wav():
    data = pcm_wav(np.zeros((1600, 2), dtype=np.float32))
    with wave.open(io.BytesIO(data), "rb") as reader:
        assert reader.getnchannels() == 1
        assert reader.getframerate() == 16000
        assert reader.getnframes() == 1600


async def test_empty_transcript_cannot_use_chat_as_substitute(credentials):
    context = Context()
    context.add_chat(time.time(), "Make up a summary")
    ai = OpenAIContext(credentials)
    with pytest.raises(ValueError, match="real audio"):
        await ai.summarize(context, ChannelConfig(), time.time())


async def test_summary_uses_structured_output_no_storage_and_actual_transcript_evidence(
    credentials,
):
    context = Context()
    now = time.time()
    context.add_transcript(now, "We are building a castle in this game.")
    ai = OpenAIContext(credentials)
    parse = AsyncMock(
        return_value=SimpleNamespace(
            output_parsed=SummaryContent(
                activity="We are building a castle.", evidence=["building a castle"]
            )
        )
    )
    ai._client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    ai._key = "fake"
    credentials.set("openai_api_key", "fake")
    summary = await ai.summarize(context, ChannelConfig(), now)
    assert summary.evidence == ["building a castle"]
    assert parse.call_args.kwargs["store"] is False
    assert parse.call_args.kwargs["text_format"] is SummaryContent


async def test_fabricated_evidence_is_discarded(credentials):
    now = time.time()
    context = Context()
    context.add_transcript(now, "We are exploring the cave.")
    ai = OpenAIContext(credentials)
    parse = AsyncMock(
        return_value=SimpleNamespace(
            output_parsed=SummaryContent(
                activity="We won a championship.", evidence=["won a championship"]
            )
        )
    )
    ai._client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    ai._key = "fake"
    credentials.set("openai_api_key", "fake")
    with pytest.raises(ValueError, match="actual transcript"):
        await ai.summarize(context, ChannelConfig(), now)
