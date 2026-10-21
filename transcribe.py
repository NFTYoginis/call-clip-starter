#!/usr/bin/env python3
"""transcribe.py: word-level transcript of a recording, locally, free.

    python3 transcribe.py my-call.mp4            # writes my-call.asr.json next to it

Needs:  pip install openai-whisper   and   ffmpeg on your PATH.
Model:  "small" is a good default on a laptop. Use --model medium for accents or jargon.
Long calls: this loads the whole file's audio. For 60+ minutes, trim the window you
care about first (ffmpeg -ss <in> -to <out>) and pass --offset to cut.py later.
"""
import argparse
import json
import pathlib

import whisper


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--model", default="small")
    ap.add_argument("--language", default="en")
    a = ap.parse_args()

    model = whisper.load_model(a.model)
    r = model.transcribe(a.media, word_timestamps=True, language=a.language, fp16=False)
    out = pathlib.Path(a.media).with_suffix(".asr.json")
    out.write_text(json.dumps({"segments": r["segments"]}, indent=1))
    n = sum(len(s.get("words", [])) for s in r["segments"])
    print(f"{n} words -> {out}")

    # A readable version with timestamps, so you can pick your moments by reading.
    lines = []
    for s in r["segments"]:
        lines.append(f"[{s['start']:8.2f} -> {s['end']:8.2f}]  {s['text'].strip()}")
    txt = out.with_suffix(".txt")
    txt.write_text("\n".join(lines) + "\n")
    print(f"readable transcript -> {txt}")


if __name__ == "__main__":
    main()
