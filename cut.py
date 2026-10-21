#!/usr/bin/env python3
"""cut.py: cut moments out of a recording at WORD boundaries, keep captions in sync.

    python3 cut.py plan.json            # cut + write remotion/public/clip.mp4 and remotion/src/words.json
    python3 cut.py plan.json --check    # only audit the plan, write nothing

plan.json:
    {
      "video": "/path/to/recording.mp4",
      "asr":   "/path/to/recording.asr.json",   # from transcribe.py
      "asr_offset": 0.0,                         # only if the ASR was run on a trimmed window
      "fps": 30,
      "chunks": [[83.2, 91.5], [140.0, 152.3]]   # [in, out] seconds in the recording
    }

Two rules this enforces (both learned the hard way):

1. NO CUT LANDS INSIDE A WORD. If an in/out point falls inside a spoken word, it is
   moved to just outside that word, and the move is printed. You never get a clipped
   syllable or a stutter at a splice. Cutting by timecode is how mid-word cuts happen;
   the transcript knows where the words are, so the tool uses it.

2. A WORD BELONGS TO THE CHUNK CONTAINING ITS MIDPOINT. A word straddling a splice
   would otherwise get a start inside the cut and an end outside it, which renders as
   a caption that lights up and never turns off.

Needs: ffmpeg + ffprobe on PATH.
"""
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PAD = 0.03        # s of breathing room outside a word when we snap to it
SEAM_FADE = 0.04  # s audio fade at each splice, kills the click without eating a consonant


def load_words(asr_path, offset):
    d = json.loads(pathlib.Path(asr_path).read_text())
    return [
        {"w": w["word"].strip(), "s": w["start"] + offset, "e": w["end"] + offset}
        for sg in d["segments"] for w in sg.get("words", [])
    ]


def snap(t, words, kind):
    """Return (new_t, moved_word_or_None). kind is 'in' or 'out'."""
    for i, w in enumerate(words):
        if w["s"] < t < w["e"]:
            if kind == "in":
                prev_e = words[i - 1]["e"] if i else 0.0
                new = max(w["s"] - PAD, (prev_e + w["s"]) / 2)
            else:
                nxt_s = words[i + 1]["s"] if i + 1 < len(words) else w["e"] + 1
                new = min(w["e"] + PAD, (w["e"] + nxt_s) / 2)
            return round(new, 3), w["w"]
    return t, None


def audit(chunks, words):
    out, moved = [], 0
    for a, b in chunks:
        a2, wa = snap(a, words, "in")
        b2, wb = snap(b, words, "out")
        for kind, old, new, w in (("in", a, a2, wa), ("out", b, b2, wb)):
            if w:
                moved += 1
                print(f"  {kind:>3} {old:.2f}s is inside \"{w}\" -> moved to {new:.2f}s")
        out.append((a2, b2))
    return out, moved


def remap(words, chunks):
    base, acc = [], 0.0
    for a, b in chunks:
        base.append(acc)
        acc += b - a
    out = []
    for x in words:
        mid = (x["s"] + x["e"]) / 2
        for i, (a, b) in enumerate(chunks):
            if a <= mid < b:
                out.append({
                    "w": x["w"],
                    "s": round(max(0.0, x["s"] - a) + base[i], 3),
                    "e": round(min(b - a, x["e"] - a) + base[i], 3),
                    "chunk": i,
                })
                break
    out.sort(key=lambda z: z["s"])
    return out, acc


def cut_video(src, chunks, fps, out_path):
    ff = shutil.which("ffmpeg")
    if not ff:
        sys.exit("ffmpeg not found on PATH")
    tmp = HERE / ".parts"
    tmp.mkdir(exist_ok=True)
    parts = []
    for i, (a, b) in enumerate(chunks):
        d = b - a
        p = tmp / f"part{i:02d}.mp4"
        # Re-encode every part the same way so the concat below is safe.
        subprocess.run([
            ff, "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", src,
            "-vf", f"fps={fps},format=yuv420p",
            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
            "-af", f"afade=t=in:st=0:d={SEAM_FADE},afade=t=out:st={d - SEAM_FADE:.3f}:d={SEAM_FADE}",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k", str(p),
        ], check=True)
        parts.append(p)
    (tmp / "list.txt").write_text("".join(f"file '{p.name}'\n" for p in parts))
    subprocess.run([ff, "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(tmp / "list.txt"), "-c", "copy", str(out_path)], check=True)
    shutil.rmtree(tmp)


def probe_size(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True).stdout.strip().split(",")
    return int(r[0]), int(r[1])


def main():
    plan = json.loads(pathlib.Path(sys.argv[1]).read_text())
    check_only = "--check" in sys.argv
    words = load_words(plan["asr"], plan.get("asr_offset", 0.0))
    chunks, moved = audit([tuple(c) for c in plan["chunks"]], words)
    print(f"{len(chunks)} chunk(s), {moved} cut point(s) moved off a word")
    if check_only:
        return 0

    out_vid = HERE / "remotion" / "public" / "clip.mp4"
    cut_video(plan["video"], chunks, plan["fps"], out_vid)
    reel_words, dur = remap(words, chunks)
    w, h = probe_size(out_vid)
    (HERE / "remotion" / "src" / "words.json").write_text(json.dumps(
        {"dur": round(dur, 3), "fps": plan["fps"], "width": w, "height": h, "words": reel_words}, indent=0))
    print(f"clip.mp4 {dur:.2f}s ({w}x{h}), {len(reel_words)} words -> remotion/src/words.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
