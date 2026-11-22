"""End-to-end test with no network: fake LLM, fake TTS, code-drawn backgrounds. Needs ffmpeg."""
import json
import shutil
import subprocess

from toonshorts import free_ai, pipeline

SCRIPT = {"title": "The island ruled by rabbits", "hook_text": "RABBIT ISLAND",
          "scenes": [{"background": "small island beach", "cast": ["MILO", "ZARA"], "lines": [
              {"who": "MILO", "text": "This whole island is ruled by rabbits!"},
              {"who": "ZARA", "text": "Hundreds of feral rabbits roam the island."},
              {"who": "KIKO", "text": "Where is my snack?"},
              {"who": "MILO", "text": "I bet they hold meetings every morning and vote on carrot prices."},
              {"who": "ZARA", "text": "Not quite, but visitors can walk the whole island in an afternoon."}]},
              {"background": "grass field with a lighthouse", "cast": ["ZARA", "KIKO"], "lines": [
              {"who": "ZARA", "text": "The island is about four kilometres around."},
              {"who": "MILO", "text": "Tiny island, giant fluffy army!"},
              {"who": "KIKO", "text": "I am staying in the boat, thank you very much."},
              {"who": "MILO", "text": "Fine, more rabbit cuddles for me and my camera then."},
              {"who": "ZARA", "text": "Would you visit? Tell us in the comments!"}]}],
          "source_sentences": ["Hundreds of feral rabbits roam the island.",
                               "The island is about 4.3 kilometres in circumference."],
          "description": "d", "tags": ["rabbits"], "hashtags": ["#travel"]}
SOURCE_TEXT = ("Okunoshima is a small island in Japan. Hundreds of feral rabbits roam the island. "
               "The island is about 4.3 kilometres in circumference. ") * 20


def fake_tts(text, mp3, voice, rate, pitch):
    dur = 0.3 * len(text.split()) + 0.2
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=220:duration={dur}",
                    "-ar", "24000", str(mp3)], check=True)
    return [(i * 0.3, i * 0.3 + 0.26, w) for i, w in enumerate(text.split())]


def test_fact_check():
    assert pipeline.unverified(["Hundreds of feral rabbits roam the island."], SOURCE_TEXT) == []
    assert pipeline.unverified(["The island has ten thousand dragons living on top."], SOURCE_TEXT)


def test_full_episode(monkeypatch):
    monkeypatch.setattr(free_ai, "locucao_edge", fake_tts)
    monkeypatch.setattr(free_ai, "gerar_cenario", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline")))
    monkeypatch.setattr(pipeline, "wikipedia", lambda t, lang="en": {"title": "Okunoshima", "url": "u", "text": SOURCE_TEXT})
    monkeypatch.setattr(pipeline, "youtube_searches", lambda ch, t: [])
    monkeypatch.setattr(pipeline, "llm", lambda ch, p: (json.loads(json.dumps(SCRIPT)), "fake"))
    ch = pipeline.Channel("world-tour-toons")
    try:
        out = pipeline.run("world-tour-toons", upload=False, force=True)
        assert out.exists() and out.stat().st_size > 100_000
    finally:
        shutil.rmtree(ch.dir / "output", ignore_errors=True)
        shutil.rmtree(ch.dir / ".cache", ignore_errors=True)
        (ch.dir / "history.json").unlink(missing_ok=True)
