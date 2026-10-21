# call-clip-starter

Cut short, captioned clips out of a long recording: a call, a webinar, a screen share. Each caption is timed to the word it belongs to, and if a cut point would land inside a spoken word, the tool moves it just outside that word.

Built by The Quiet Scribe.

![three frames from a sample clip](docs/preview.png)

Four steps, three small tools:

```
recording ──▶ transcribe.py ──▶ you pick moments ──▶ cut.py ──▶ Remotion ──▶ clip.mp4
              (whisper, local)   (read the .txt)     (word-safe)  (captions)
```

## Quick start

You need Python 3.9+, Node 18+, and [ffmpeg](https://ffmpeg.org) on your PATH.

```bash
git clone <this repo> && cd call-clip-starter
pip install -r requirements.txt
(cd remotion && npm install)
```

**First, run the sample.** The repo ships with a tiny test clip, so you can see what the captions look like before you touch your own recording:

```bash
cd remotion && npm run dev
```

**1. Transcribe.** Whisper runs on your own computer. It writes `my-call.asr.json` and a readable `my-call.asr.txt` next to the recording.

```bash
python3 transcribe.py my-call.mp4
```

**2. Pick your moments.** Open the `.txt`. Every line has timestamps, so you choose clips by reading. Copy `plan.example.json` to `plan.json` and fill it in:

```json
{
  "video": "/path/to/my-call.mp4",
  "asr": "/path/to/my-call.asr.json",
  "fps": 30,
  "chunks": [[83.2, 91.5], [140.0, 152.3]]
}
```

Each chunk is `[in, out]` in seconds. One chunk gives you one moment. Several chunks are joined into one clip.

**3. Cut.** To see what would change without writing anything, run the check first (`--check` writes nothing):

```bash
python3 cut.py plan.json --check
python3 cut.py plan.json
```

If an in or out point lands inside a spoken word, `cut.py` moves it to just outside that word and tells you which one. It can only do this for words Whisper heard.

**4. Render.**

```bash
cd remotion
npm run dev       # preview and tweak in the browser
npm run render    # writes remotion/out/clip.mp4
```

`cut.py` overwrites the sample with your clip.

## Why the captions stay in step

- **The timings come from the transcript.** Each word has its own start and end time. Nothing is spread evenly across a sentence.
- **A word belongs to the chunk that holds its midpoint.** Otherwise a word that straddles a join would start inside the cut and end outside it, and its caption would light up and never turn off.
- **Every join starts a new caption line.** A line never reads half from one moment and half from another.

## Make it yours

Everything visual is in [`remotion/src/Clip.tsx`](remotion/src/Clip.tsx): colours, font, words per line, layout. The top of the file holds the settings. The video is 1080x1920 (vertical). To get 16:9 or square, change it in `Root.tsx`.

## Honest limits

- Whisper mishears names and jargon. Read the caption text before you post. `small` is the default model, and `--model medium` helps.
- A cut can still land inside a word that Whisper missed.
- This is not a full editor. It does not cut dead air and it does not crop to a speaker's face. It is the spine of one.
- A wide screen recording sits small in the vertical frame, so on-screen text can be hard to read. For text-heavy recordings, change the layout to 16:9 in `Root.tsx` and `Clip.tsx`.
- It does not tell speakers apart. With more than one voice, check who is speaking before you cut.
- Every chunk is re-encoded, so it is not a straight copy of your video.
- Tested on macOS only so far (Whisper `base` and `small`). Other platforms may work. We have not run them.
- Long recordings, an hour or more: trim the stretch you care about with ffmpeg first, transcribe that, and set `asr_offset` in the plan to the time where the stretch started.
- If other people are on the recording, get their yes before you post a clip. The tool does not ask for you.

## Not ready to code?

Descript, where you edit the transcript like a document, or CapCut, with automatic word-by-word captions, will get you most of the way with no setup. This repo earns its place once you are cutting the same kind of clip again and again.

## Want help?

Want help installing this or learning it? The Quiet Ai can help: [thequietscribe.com](https://thequietscribe.com). There is also a free community, Wellness & AI, at [skool.com/wellness-and-ai/about](https://skool.com/wellness-and-ai/about).

## Licence

Our own code is MIT. That covers only what is in this repo.

Remotion, which draws the captions, is a separate dependency under its own licence. It is source-available, not open source, and our MIT licence gives you no rights to it. Remotion is free for individuals and for teams of up to 3 people, contractors included. A company of 4 or more needs a Remotion Company License. The count is the size of the whole company, not the number of people who use Remotion. If you set this up for a client who will run it, both headcounts are added together. You are responsible for checking that you qualify: [remotion.dev/docs/license](https://www.remotion.dev/docs/license) and [remotion.pro/license](https://www.remotion.pro/license).

Remotion may change its terms in a future version, so read them again when you update it. The current terms are at the two links above.
