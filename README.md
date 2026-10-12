# CheckAI

Tell whether a piece of text was written by AI or by a person. CheckAI runs entirely on your own computer, never sends your text anywhere, and comes as a web app, a command-line tool, and a zero-install browser page.

The result is a **probability, not proof**. Use it to find the parts of a text that sound machine-made and rewrite them, not to accuse anyone.

## How it scores text

The final score combines two parts. The language model counts for 70% when it is running.

1. **A language model, using the Binoculars method** (Hans et al., 2024). Two Qwen2.5 models, a base and an instruct version, read the text:
   - *log-perplexity* measures how predictable each word is to the model. AI text is unusually predictable.
   - *cross-perplexity* measures how predictable the model expects text to be at that point.
   - **Binoculars score = log-perplexity ÷ cross-perplexity.** Below the threshold means AI-like. Dividing by cross-perplexity stops naturally predictable topics, like formal or technical writing, from being flagged.
   - Each sentence is scored on its own too, so you can see which sentences look most machine-made.
2. **Six writing-style signals** that need no model:
   - even sentence lengths
   - AI buzzwords ("delve", "seamless", "a testament to")
   - stock transitions at the start of sentences ("Moreover", "Furthermore")
   - no personal voice (no contractions, first person or casual words)
   - repeated vocabulary
   - repeated three-word phrases

## Install

You need Python 3.10 or newer.

```bash
git clone https://github.com/kipoikibo995-sys/checkai
cd checkai
pip install -r requirements.txt
```

The first run downloads the models from Hugging Face. The default `light` preset is about 2 GB, and later runs reuse the download.

If you don't want to install the model libraries, add `--no-model` to any command. CheckAI then uses the six writing-style signals only and works with plain Python.

## Use it

**Web app** (easiest):

```bash
python -m aicheck serve
```

Then open http://127.0.0.1:8000, paste your text and press **Check text** (or Ctrl+Enter).

**Command line:**

```bash
python -m aicheck check samples/ai-sample.txt       # one file
python -m aicheck check articles/                   # every .txt file in a folder
python -m aicheck check post.txt --json > result.json
echo "Paste text here..." | python -m aicheck check
```

**Browser only:** open `browser/index.html` from any web host (GitHub Pages, Vercel, or `python -m http.server -d browser`). It starts with the writing-style signals. Press **Turn on AI model** to download two small language models (SmolLM2-135M base and instruct, about 275 MB, once) that run the Binoculars check inside the browser with [transformers.js](https://huggingface.co/docs/transformers.js). Your text still never leaves the device. The browser keeps the models cached and turns them back on automatically on later visits.

**Deploy on Vercel:** import this repo in Vercel and deploy with the default settings. `vercel.json` tells Vercel to serve the `browser/` folder as a static site, and `.vercelignore` leaves the Python app out. The language model runs in each visitor's browser, so no server or paid plan is needed.

### Choosing a model

| Option | Models | Needs |
|---|---|---|
| `--preset light` (default) | Qwen2.5-0.5B + Instruct | about 4 GB RAM, runs on CPU |
| `--preset standard` | Qwen2.5-1.5B + Instruct | about 12 GB RAM, or an 8 GB GPU |
| `--preset strong` | Qwen2.5-7B + Instruct | a GPU with 24 GB or more |
| `--single` | base model only | half the memory, less accurate |

You can also pass any other pair with `--observer` and `--performer`, as long as both models come from the same family and share a vocabulary.

## Run it online for free (Hugging Face Spaces)

A free Hugging Face Space (CPU Basic) has enough memory for the `light` model pair, so you get a public link with the full model.

1. Sign in at https://huggingface.co and click **New Space**.
2. Name it (for example `checkai`), choose **Docker** as the SDK and **Blank** as the template, keep the free **CPU Basic** hardware, and create the Space.
3. In the Space, open **Files**, click **Add file → Upload files**, and upload `deploy/huggingface/Dockerfile` from this repo. Optionally replace the Space's `README.md` with `deploy/huggingface/README.md`.
4. The Space builds by itself. The first build downloads PyTorch and the models, so it takes a while. When it shows **Running**, the app is live at `https://huggingface.co/spaces/<your-name>/checkai`.

To pick up new code from GitHub later, open the Space **Settings** and click **Factory rebuild**. On CPU each check takes a few seconds, and a free Space sleeps after a period without visitors, so the first visit after that is slow.

## Run it on a free Oracle Cloud server

Oracle Cloud's Always Free tier includes an Arm server with enough memory for the full app.

1. Sign up at https://www.oracle.com/cloud/free/ (a card is needed for verification).
2. Go to **Compute → Instances → Create instance**.
   - **Image:** Canonical Ubuntu 24.04 (or 22.04).
   - **Shape:** Ampere `VM.Standard.A1.Flex` with 2 OCPUs and 12 GB memory.
   - **Networking:** keep the new virtual cloud network and make sure a public IPv4 address is assigned.
   - **SSH keys:** let Oracle generate a key pair and download it.
   - **Advanced options → Management:** choose **Paste cloud-init script** and paste all of `deploy/oracle/cloud-init.sh`.
3. Click **Create**.
4. Open port 80: on the instance page click the **subnet**, then its **Default security list**, **Add ingress rules**, source CIDR `0.0.0.0/0`, IP protocol TCP, destination port `80`.
5. Wait 15–25 minutes for the first build, then open `http://<public IP>` in a browser.

To update to the latest code later, connect over SSH and run `sudo checkai-update`. The setup log is in `/var/log/checkai-setup.log`.

## Calibration (recommended)

The default threshold of 0.90 comes from the original paper, which used different models, so it may be off for Qwen. To make CheckAI accurate for the kind of writing you check, calibrate it with your own samples:

1. Put `.txt` files you know were written by people in `samples/human/`. Older posts from before 2022 work well.
2. Put `.txt` files written by ChatGPT, Claude, Gemini and similar tools on the same topics in `samples/ai/`.
3. Aim for 20 or more files of each kind, each over 150 words. Then run:

```bash
python -m aicheck calibrate --human samples/human --ai samples/ai
```

CheckAI prints the new threshold and its accuracy on your samples, and saves it to `~/.aicheck/calibration.json`. Every later check with the same model pair uses it automatically.

## Limits

- Texts under about 120 words give unreliable results.
- Formulaic human writing, such as reports, templates or SEO copy, can be flagged as AI.
- AI text that was heavily edited by hand, or rewritten by another AI, is hard to catch.
- No detector is 100% accurate, including GPTZero and Turnitin.

## Project layout

```
aicheck/heuristics.py   the six writing-style signals
aicheck/model.py        Binoculars scoring with a language model
aicheck/detector.py     combines scores, gives the verdict, handles calibration
aicheck/server.py       local web server (standard library only)
aicheck/web.html        web app UI; also works without the server
aicheck/__main__.py     command line
deploy/huggingface/     Dockerfile (also used by the Oracle setup) and Space settings
deploy/oracle/          one-paste setup script for an Oracle Cloud server
browser/index.html      copy of the web app for opening without Python
samples/                one AI-style and one human-style sample
tests/                  run with: python -m unittest discover -s tests
```

The phrase lists in `aicheck/heuristics.py` are mirrored in `aicheck/web.html`. If you edit one, update the other and copy `web.html` to `browser/index.html`.

### Browser model accuracy

The in-browser model's threshold was calibrated inside Chromium on 116 answers from the [HC3](https://huggingface.co/datasets/Hello-SimpleAI/HC3) dataset (human answers vs. ChatGPT answers from 2022) and tested on 114 different ones. See `LMCFG` in `aicheck/web.html` for the numbers it uses. Newer AI models write less predictably than 2022 ChatGPT, so expect it to miss more of their text: a "human" verdict means "not obviously AI", not proof.
