import { AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import data from "./words.json";

type Wd = { w: string; s: number; e: number; chunk: number };
const WORDS = data.words as Wd[];

// ---- the look: change these ----
const BG = "#F7F3E8";
const INK = "#1D2B33";
const ACTIVE = "#B8801A";
const FONT = "Georgia, 'Times New Roman', serif";
const MAX_WORDS = 4;   // words per caption line
const GAP = 0.35;      // s of silence that always starts a new line

// Split the words into caption lines: break at every splice, on a pause, on
// sentence-ending punctuation, or when a line hits MAX_WORDS.
const LINES: Wd[][] = [];
WORDS.forEach((w, i) => {
  const prev = WORDS[i - 1];
  const cur = LINES[LINES.length - 1];
  const brk = !cur || cur.length >= MAX_WORDS || (prev && (w.chunk !== prev.chunk || w.s - prev.e > GAP || /[.?!]$/.test(prev.w)));
  if (brk) LINES.push([w]);
  else cur.push(w);
});

export const Clip = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // The current line is the last one that has started; it stays up through the pause after it.
  let li = -1;
  LINES.forEach((l, i) => { if (t >= l[0].s) li = i; });
  const line = li >= 0 ? LINES[li] : [];
  const lineEnd = line.length ? line[line.length - 1].e + 0.4 : 0;
  const show = line.length > 0 && t < lineEnd;

  const aspect = data.width / data.height;
  const vidH = Math.round(1080 / aspect);

  return (
    <AbsoluteFill style={{ background: BG }}>
      {/* the recording, full width, top-aligned */}
      <div style={{ position: "absolute", left: 0, top: 120, width: 1080, height: vidH, borderRadius: 24, overflow: "hidden", boxShadow: "0 12px 40px rgba(0,0,0,0.18)" }}>
        <OffthreadVideo src={staticFile("clip.mp4")} style={{ width: "100%", height: "100%" }} />
      </div>

      {/* captions, one line at a time, the spoken word lit */}
      {show && (
        <div style={{ position: "absolute", left: 60, right: 60, top: 120 + vidH, bottom: 0, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", fontFamily: FONT, fontWeight: 700, fontSize: 92, lineHeight: 1.15 }}>
          <div>
            {line.map((w, i) => (
              <span key={i} style={{ color: t >= w.s && t < w.e ? ACTIVE : INK }}>{w.w}{" "}</span>
            ))}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
