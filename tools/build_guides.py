"""Build the Koji AI Checker guide pages into browser/<slug>/index.html."""
import html
import json
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
SITE = "https://kojicheck.kojilaunch.com/"
DATE = "2026-11-10"
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 37'%3E%3Cpath d='M10 0h12a17.5 17.5 0 0 1 0 35H10z' "
           "fill='%23f05216'/%3E%3Cpath d='M0 6h4a9 9 0 0 1 9 9v22H0z' fill='%23081c25'/%3E%3C/svg%3E")

HEADER = """<header class="site-head" id="siteHead">
  <div class="site-nav">
    <div class="site-id">
      <a class="site-logo" href="https://kojilaunch.com/"><span class="brand-mark" aria-hidden="true"></span>KoJi Academy</a>
      <a class="site-tool" href="/">AI Checker</a>
    </div>
    <nav class="site-links" id="siteLinks" aria-label="Main navigation">
      <a href="https://kojilaunch.com/about/">About</a>
      <a href="https://kojilaunch.com/my-blog/">Journal</a>
      <a href="https://kojilaunch.com/reviews/">Reviews</a>
      <a href="https://kojilaunch.com/my-product/">Products</a>
      <a href="https://kojilaunch.com/gifts/">Resources</a>
      <a href="https://kojilaunch.com/stream-writer-jv/">Affiliate</a>
      <a class="nav-member" href="https://kojilaunch.com/login/?redirect_to=https%3A%2F%2Fkojilaunch.com%2Fmember-dashboard%2F">Member Access</a>
    </nav>
    <button class="site-toggle" id="siteToggle" type="button" aria-expanded="false" aria-controls="siteLinks" aria-label="Open site menu">☰</button>
    <a class="member" href="https://kojilaunch.com/login/?redirect_to=https%3A%2F%2Fkojilaunch.com%2Fmember-dashboard%2F">Member Access</a>
  </div>
</header>"""

FOOTER = """<footer class="site-foot">
  <div class="foot-wrap">
    <div class="foot-top">
      <div>
        <a class="site-logo" href="https://kojilaunch.com/"><span class="brand-mark" aria-hidden="true"></span>KoJi Academy</a>
        <p>Documenting the blueprint for sovereignty in the digital age.</p>
      </div>
      <div class="foot-cols">
        <nav class="foot-col" aria-label="AI Checker"><b>AI Checker</b>
          <a href="/">Free AI detector</a>
          <a href="/chatgpt-detector/">ChatGPT detector</a>
          <a href="/ai-detector-for-kdp/">AI detector for KDP authors</a>
          <a href="/how-to-check-if-text-is-ai-written/">How to check if text is AI-written</a>
        </nav>
        <nav class="foot-col" aria-label="Programs"><b>Programs</b>
          <a href="https://kojilaunch.com/saas-vibe-coding/">SaaS &amp; Vibe Coding</a>
          <a href="https://kojilaunch.com/lets-build-your-website/">Websites</a>
          <a href="https://kojilaunch.com/stream-writer-jv/">Partner program</a>
          <a href="https://kojilaunch.com/contactus/">1:1 Coaching</a>
        </nav>
        <nav class="foot-col" aria-label="Resources"><b>Resources</b>
          <a href="https://kojilaunch.com/7-day-roadmap/">7-Day Roadmap</a>
          <a href="https://kojilaunch.com/gifts/">Free Resources</a>
          <a href="https://kojilaunch.com/my-blog/">Journal</a>
        </nav>
        <nav class="foot-col" aria-label="Company"><b>Company</b>
          <a href="https://kojilaunch.com/about/">About</a>
          <a href="https://kojilaunch.com/contactus/">Contact</a>
          <a href="https://kojilaunch.com/privacy-policy/">Privacy Policy</a>
          <a href="https://kojilaunch.com/terms-of-service/">Terms of Service</a>
        </nav>
      </div>
    </div>
    <div class="foot-bottom">© 2026 KoJi Academy. All rights reserved.</div>
  </div>
</footer>
<script>
document.getElementById("siteToggle").onclick = () => {
  const o = document.getElementById("siteHead").classList.toggle("open");
  document.getElementById("siteToggle").setAttribute("aria-expanded", String(o));
};
</script>"""

GUIDES = {
    "chatgpt-detector": ("ChatGPT detector", "How ChatGPT text gives itself away, and how accurate a check can be."),
    "ai-detector-for-kdp": ("AI detector for KDP authors", "Check a book manuscript privately before you publish."),
    "how-to-check-if-text-is-ai-written": ("How to check if text is AI-written", "A step-by-step method that does not rely on one score."),
}


def cta(text="Paste your text and get a score in seconds. Free, no sign-up, and your text never leaves your device."):
    return f"""<div class="cta"><p><b>Check your text with Koji AI Checker</b>{text}</p><a class="btn" href="/">Check text free</a></div>"""


def page(slug, title, desc, h1, eyebrow, lede, body, faq):
    url = f"{SITE}{slug}/"
    faq_html = "\n".join(f"<h3>{html.escape(q)}</h3>\n<p>{a}</p>" for q, a in faq)
    related = "\n".join(f'<a href="/{s}/">{html.escape(t)}<span>{html.escape(d)}</span></a>'
                        for s, (t, d) in GUIDES.items() if s != slug)
    strip = lambda s: html.unescape(__import__("re").sub(r"<[^>]+>", "", s))
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": desc, "url": url,
         "datePublished": DATE, "dateModified": DATE, "inLanguage": "en", "image": SITE + "og.png",
         "author": {"@type": "Organization", "name": "KoJi Academy", "url": "https://kojilaunch.com/"},
         "publisher": {"@type": "Organization", "name": "KoJi Academy", "url": "https://kojilaunch.com/"},
         "mainEntityOfPage": url},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Koji AI Checker", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": GUIDES[slug][0], "item": url}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in faq]},
    ]
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#f05216">
<meta property="og:type" content="article">
<meta property="og:site_name" content="KoJi Academy">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{SITE}og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{SITE}og.png">
<link rel="icon" href="{FAVICON}">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700;9..40,800;9..40,900&display=swap">
<link rel="stylesheet" href="/assets/guide.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
{HEADER}
<main class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Koji AI Checker</a> › {html.escape(GUIDES[slug][0])}</nav>
<article>
<p class="eyebrow">{html.escape(eyebrow)}</p>
<h1>{html.escape(h1)}</h1>
<p class="lede">{lede}</p>
<p class="meta">By KoJi Academy · Updated {DATE}</p>
{body}
<section class="faq" aria-labelledby="faq">
<h2 id="faq">Frequently asked questions</h2>
{faq_html}
</section>
</article>
<h2>More guides</h2>
<div class="related">
{related}
<a href="/">Koji AI Checker<span>The free AI detector itself.</span></a>
</div>
</main>
{FOOTER}
</body>
</html>
"""
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(doc, encoding="utf-8")
    words = len(strip(body + faq_html + lede).split())
    print(f"{slug}: {words} words, title {len(title)} chars, description {len(desc)} chars")


# ---------------------------------------------------------------- KDP
page(
    "ai-detector-for-kdp",
    "AI Detector for KDP Authors: Check Your Manuscript | Koji",
    "Check a KDP book manuscript for AI-written passages before you publish. Free, private (your text never leaves your device) and honest about its limits.",
    "AI detector for KDP authors",
    "For self-publishers",
    "Before you upload a book to Amazon KDP, it helps to know which passages read as machine-written. Koji AI Checker checks your manuscript inside your browser, so unpublished chapters are never uploaded anywhere.",
    f"""
{cta("Check a chapter now. Your manuscript stays on your computer: nothing is uploaded or stored.")}

<h2>Why KDP authors check their manuscripts</h2>
<p>When you publish or republish a book, KDP asks whether it contains AI-generated content. Many authors now work with AI in some way, whether for brainstorming, outlining, editing or translation, and with ghostwriters or co-authors whose process they cannot fully see. A detector does not answer the KDP question for you, but it helps you spot the passages worth a second look:</p>
<ul>
<li><b>Ghostwritten or outsourced chapters.</b> If you paid for writing, a check is a quick way to see whether some sections read like raw AI output before your name goes on the cover.</li>
<li><b>Your own AI-assisted drafts.</b> If you used AI to draft and then rewrote, a check shows which sections still read like the original output and may deserve another pass in your own voice.</li>
<li><b>Reader trust.</b> Readers leave reviews when a book feels generic. The phrases AI overuses, such as "a testament to", "delve into" or "in today's fast-paced world", are exactly what readers notice.</li>
</ul>

<h2>What KDP asks about AI content</h2>
<p>KDP's content guidelines ask publishers to tell Amazon when a book contains <b>AI-generated</b> text, images or translations. They describe <b>AI-assisted</b> work differently: if you created the content yourself and used AI tools to edit, refine, error-check or brainstorm, KDP treats that as AI-assisted. Where exactly a heavily edited AI draft falls is something authors and guides disagree about, so read the rules in Amazon's own words before you decide.</p>
<div class="note"><p>This page is general information, not legal or policy advice. The rules can change: always check Amazon's current <a href="https://kdp.amazon.com/en_US/help/topic/G200672390" rel="noopener" target="_blank">KDP Content Guidelines</a> before you publish.</p></div>
<p>A detector score is not part of that decision. KDP asks how the content was <i>made</i>, which you know better than any tool. Use the checker to find passages you want to rewrite, not to decide what to declare.</p>

<h2>How to check a manuscript with Koji AI Checker</h2>
<ol>
<li><b>Work chapter by chapter.</b> The AI model reads up to about 512 tokens (roughly 350 to 400 English words) at a time, so paste one scene or a section of 150 to 400 words per check. Long chapters are best checked in a few parts.</li>
<li><b>Turn on the AI model.</b> On a computer, choose the Accurate model (a one-time download of about 730 MB that stays in your browser). On a phone, the Lite model (about 275 MB) is suggested.</li>
<li><b>Read the reasons, not only the number.</b> The result lists the buzzwords and stock transitions it found and highlights them in your text, so you can see what to change.</li>
<li><b>Rewrite in your own voice and check again.</b> Specific details, opinions, varied sentence lengths and natural dialogue are what make prose read as human.</li>
</ol>
{cta()}

<h2>How to read the result</h2>
<div class="table-scroll"><table>
<tr><th>Result</th><th>What it means for your manuscript</th></tr>
<tr><td>Likely AI-written (75% and up)</td><td>The passage reads strongly like unedited AI output. If you did not expect that, find out where it came from.</td></tr>
<tr><td>Leans AI / Mixed signals</td><td>Some sentences or phrases read as machine-made. Look at the highlighted phrases first.</td></tr>
<tr><td>Leans or likely human</td><td>No strong AI signs. This is not proof of human writing: edited AI text can score low.</td></tr>
</table></div>

<h2>What a detector cannot tell you</h2>
<p>No AI detector is proof, ours included. In our tests on 114 held-out answers from the public HC3 dataset (people vs. ChatGPT), the Accurate model was right 98% of the time. Newer AI models write less predictably: on a small set of 11 texts mostly from 2026 models, it caught 6. Heavily edited or paraphrased AI text is harder still. Formal, plain prose by a person can occasionally look AI-like. Fiction with lots of dialogue usually reads as human, and so does a strong personal voice.</p>
<p>So treat the score as a pointer to passages that deserve attention, never as evidence against a ghostwriter, editor or co-author on its own. Ask for drafts, outlines or version history if you need to know how a text was written.</p>

<h2>Why privacy matters for unpublished books</h2>
<p>Many online detectors send your text to their servers, and some keep it. For an unpublished manuscript that is a real risk. Koji AI Checker runs the language model inside your own browser: your chapters are never uploaded, and the only thing saved is a short list of recent checks in your own browser, which you can clear at any time.</p>
""",
    [
        ("Does KDP use an AI detector on my book?", "Amazon does not publish how it reviews books, so we cannot say. What KDP asks is that you tell it about AI-generated content when you publish. A detector helps you review your own text; it does not replace that disclosure."),
        ("Can I check a whole book at once?", "Check it in parts. The AI model reads up to about 350 to 400 words at a time, so one scene or section per check gives the most useful result, and the highlights show you exactly where to look."),
        ("Is my manuscript uploaded anywhere?", "No. The check, including the AI model, runs inside your browser. Your text never leaves your device."),
        ("Does it work for books in other languages?", "It is built for English. German is available as an experimental option with much lower accuracy. Other languages are not supported."),
    ],
)

# ---------------------------------------------------------------- ChatGPT
page(
    "chatgpt-detector",
    "ChatGPT Detector: Check If Text Was Written by ChatGPT | Koji",
    "Free ChatGPT detector that runs in your browser. See how likely a text was written by ChatGPT, which phrases give it away, and how accurate the check is.",
    "ChatGPT detector",
    "Free · private · no sign-up",
    "Koji AI Checker is a free ChatGPT checker: it estimates how likely a text was written by ChatGPT or a similar AI model, shows the phrases that give it away, and runs entirely in your browser.",
    f"""
{cta("Paste the text you want to check. It is scored on your device and never uploaded.")}

<h2>How ChatGPT writing gives itself away</h2>
<p>Large language models such as ChatGPT write by picking likely next words. That leaves patterns a person rarely produces all at once:</p>
<ul>
<li><b>Unusually predictable wording.</b> Each word is close to what a language model would expect next. This is the strongest signal, and the one our AI model measures.</li>
<li><b>Buzzwords and stock phrases</b> such as "delve into", "a testament to", "plays a crucial role", "seamless" or "in today's fast-paced world".</li>
<li><b>Stock transitions</b> at the start of sentences: "Moreover", "Furthermore", "Additionally", "In conclusion".</li>
<li><b>Even sentence lengths.</b> People mix short and long sentences; unedited AI text is often strikingly regular.</li>
<li><b>Little personal voice.</b> Few contractions, opinions, specific memories or first-person details.</li>
</ul>
<p>None of these alone proves anything. Together, they make a text read as machine-made, and that is what the checker scores.</p>

<h2>How the check works</h2>
<p>The score combines two parts. The larger part (70%) comes from two small language models from the SmolLM2 family that run in your browser. They use the <b>Binoculars</b> method: they measure how predictable each word is, then compare that with how predictable a model would expect the text to be. Dividing the two keeps naturally predictable topics, such as technical or formal writing, from being flagged just for being plain. The other 30% comes from the six writing-style signals listed above.</p>
<p>Because everything runs on your device, the first time you turn on the AI model your browser downloads it once (about 730 MB for the Accurate model, or 275 MB for the Lite model on phones). After that it loads from your browser in a few seconds.</p>
{cta()}

<h2>How accurate is it on ChatGPT text?</h2>
<p>We tested the checker on answers from the public <b>HC3</b> dataset, where the same questions were answered by people and by ChatGPT. On 114 answers it had not seen during setup:</p>
<div class="table-scroll"><table>
<tr><th>Model</th><th>Right overall</th><th>ChatGPT answers caught</th><th>Human answers wrongly flagged</th></tr>
<tr><td>Accurate (360M)</td><td>98%</td><td>100%</td><td>2 of 57</td></tr>
<tr><td>Lite (135M)</td><td>93%</td><td>86%</td><td>0 of 57</td></tr>
</table></div>
<p>Two honest caveats. HC3 comes from the 2022 version of ChatGPT; newer models write less predictably, and on a small set of 11 texts mostly from 2026 models the Accurate model caught only 6. And text that was edited, paraphrased or run through a "humanizer" is much harder for any detector to catch.</p>

<h2>Who uses a ChatGPT detector, and for what</h2>
<ul>
<li><b>Teachers</b> use it as a first filter on essays, then talk with the student or look at drafts before drawing any conclusion.</li>
<li><b>Editors and content managers</b> check freelance articles and spot paragraphs that read as raw AI output, so they can ask for a rewrite with real examples and sources.</li>
<li><b>Hiring teams</b> look at cover letters and writing samples, where generic AI phrasing hides what the candidate actually thinks.</li>
<li><b>Writers</b> check their own AI-assisted drafts to find the passages that still sound generic and rewrite them in their own voice.</li>
</ul>
<p>In every case the useful output is the same: the highlighted phrases and the plain-language reasons show <i>where</i> a text reads as machine-made, which is far more actionable than a single percentage.</p>

<h2>Tips for a reliable result</h2>
<ul>
<li>Check at least 150 words. Results under 120 words are unreliable.</li>
<li>Check English text. German works only as an experimental option; other languages are not supported.</li>
<li>Look at the highlighted phrases and sentences, not only the percentage.</li>
<li>Never treat one score as proof. Ask for drafts or version history if it matters how a text was written.</li>
</ul>
""",
    [
        ("Is this ChatGPT checker free?", "Yes. It is free, needs no account and has no daily limit. The AI model downloads once into your browser, and after that every check runs on your own device."),
        ("Can it detect GPT-4, GPT-5 and newer ChatGPT models?", "It looks for patterns common to large language models, so it can flag text from newer ChatGPT versions too. Newer models write less predictably, though, so expect it to miss more of their text than of older ChatGPT output."),
        ("Does it also detect Claude or Gemini?", "Yes, in the same way: it does not look for one product's fingerprint, but for the predictability and style that most AI models share."),
        ("Can students or writers be wrongly flagged?", "Yes, occasionally. In our tests the Accurate model flagged 2 of 57 human answers. Formal, plain writing and writing by non-native speakers can look more predictable. Never use a detector score as the only evidence."),
        ("Is the text I paste stored?", "No. The check runs inside your browser and nothing is uploaded. Only a short list of your recent checks is kept in your own browser, and you can clear it."),
    ],
)

# ---------------------------------------------------------------- How to
page(
    "how-to-check-if-text-is-ai-written",
    "How to Check If Text Is AI-Written: A Step-by-Step Guide | Koji",
    "How to tell if a text was written by AI: the signs to look for, how to use a free AI detector well, and why a score alone is never proof.",
    "How to check if text is AI-written",
    "Guide",
    "There is no single test that proves a text was written by AI. The reliable way combines three things: reading for the typical signs, running a detector, and looking at how the text was made.",
    f"""
<div class="note"><p><b>Short answer:</b> read the text for AI patterns, check 150+ words of it with an AI detector, and confirm with context such as drafts or version history before you draw any conclusion.</p></div>

<h2>Step 1: Read it for the typical signs</h2>
<p>AI-written text often has several of these at once. One alone means little: people use some of them too.</p>
<div class="table-scroll"><table>
<tr><th>Sign</th><th>Example</th><th>Why it can mislead</th></tr>
<tr><td>Buzzwords</td><td>"delve into", "a testament to", "seamless", "pivotal"</td><td>Marketing and business writing use them too.</td></tr>
<tr><td>Stock transitions</td><td>"Moreover," "Furthermore," "In conclusion,"</td><td>Common in school essays written by people.</td></tr>
<tr><td>Even rhythm</td><td>Every sentence 15 to 20 words long</td><td>Some careful writers are very regular.</td></tr>
<tr><td>Vague, balanced claims</td><td>"plays a crucial role in many aspects"</td><td>Summaries by people can be vague as well.</td></tr>
<tr><td>No personal voice</td><td>No "I", no opinions, no specific memories</td><td>Formal reports avoid personal voice on purpose.</td></tr>
<tr><td>Perfect but empty</td><td>No typos, no specifics, no surprises</td><td>Edited human text is also clean.</td></tr>
</table></div>

<h2>Step 2: Run an AI detector, and use it well</h2>
<p>A detector measures what you cannot see by eye: how predictable each word is to a language model. Koji AI Checker does this inside your browser and also lists the buzzwords and transitions it found.</p>
<ol>
<li>Paste at least 150 words of English text. Shorter texts give unreliable results.</li>
<li>Turn on the AI model for the best result (a one-time download that stays in your browser).</li>
<li>Read the plain-language reasons and the highlighted phrases, not only the percentage.</li>
<li>For long documents, check a few sections separately rather than one huge block.</li>
</ol>
{cta()}

<h2>Step 3: Look at how the text was made</h2>
<p>A score tells you how a text <i>reads</i>, not how it was <i>written</i>. When it matters, for example for a student essay, a freelance article or a ghostwritten book, look for evidence of the writing process:</p>
<ul>
<li><b>Version history</b> in Google Docs or Word shows whether the text grew over time or appeared in one paste.</li>
<li><b>Drafts, notes and outlines</b> are hard to fake after the fact.</li>
<li><b>A short conversation</b> about the topic usually shows quickly whether someone knows what they wrote.</li>
<li><b>Earlier writing</b> by the same person shows their normal voice and level.</li>
</ul>

<h2>Advice for teachers</h2>
<p>Set expectations before the assignment: say whether AI tools are allowed, and for what. Ask students to write in a tool with version history, or to hand in an outline or notes with the essay. If a detector flags an essay, use it to start a conversation, not to grade: ask the student to explain their argument or to talk you through how they wrote a paragraph. Students who wrote the text themselves can usually do this easily.</p>

<h2>Advice for editors and clients</h2>
<p>If you commission articles, copy or books, agree up front whether AI drafting is acceptable and whether it must be disclosed. When a piece reads as generic, the detector's highlights show which paragraphs to send back. Ask for concrete details that only real research or experience can provide: named sources, numbers, examples, quotes. Those are what generic AI text lacks, and they make the piece better whoever wrote it.</p>

<h2>What not to do</h2>
<ul>
<li><b>Do not accuse anyone on a score alone.</b> Every detector makes mistakes. In our tests the most accurate model still flagged 2 of 57 human texts, and it missed some text from newer AI models.</li>
<li><b>Do not judge very short texts.</b> Under about 120 words there is too little to measure.</li>
<li><b>Do not rely on one tool.</b> If it matters, compare a second detector and, above all, the context from step 3.</li>
<li><b>Do not paste confidential text into tools that upload it.</b> Koji AI Checker runs in your browser, but many online detectors send text to their servers.</li>
</ul>

<h2>Why AI text is hard to prove</h2>
<p>AI models are trained on human writing, and people increasingly edit AI drafts or use AI to polish their own. The result is a spectrum, not two clean boxes. Newer models also write less predictably than older ones, and "humanizer" tools rewrite AI text specifically to avoid detection. That is why the best practice is to treat detectors as a first filter and to make decisions on the writing process, not on a percentage.</p>
""",
    [
        ("Can you tell for sure if a text was written by AI?", "Not from the text alone. Detectors and close reading give you a strong hint; drafts, version history and a conversation with the writer give you certainty."),
        ("How many words do I need to check?", "At least 150 words for a useful result. Results for texts under 120 words are unreliable."),
        ("Is a free AI detector good enough?", "For a first check, yes. Koji AI Checker was right 98% of the time on held-out ChatGPT answers in our tests, but every detector, free or paid, misses some newer and edited AI text and occasionally flags a person."),
        ("What if the detector says my own writing is AI?", "It happens, especially with formal or very plain writing. Your drafts and version history are the best way to show how you wrote it."),
    ],
)
