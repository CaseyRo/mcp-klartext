# casey

> Single Casey brand replacing the former `casey-berlin` and `cdit-works` contexts. One voice, two registers — `personal` and `professional` — sharing one voice DNA. The registers represent intent (recognition vs. verification), not different voices. Source: 7 May 2026 brand-decisions doc.

## Voice (shared across registers)

- **Perspective:** "I" — personal, first-person.
- **Register baseline:** Warm-professional with vulnerability. 65% informal, 35% professional. Knowledgeable friend over coffee, not lecturer from a stage.
- **Tone:** Reflective, metaphor-rich, self-implicated. Shows the speaker in the same mess as the reader.
- **Signature moves:** Scene drops, the pivot ("People aren't resisting AI because they're stubborn. Often they're grieving."), callbacks, quiet landings with reframed questions.
- **Closers:** Reflective question, quiet image, or reframed mantra. Rainbow emoji as occasional personal stamp.

## Hard rules (locked, May 2026)

- **No em-dashes.** Use colons, commas, semicolons, periods, parentheses.
- **No all-caps anywhere.** No exceptions.
- **Load-bearing words used sparingly** (each appears once or twice in a longer piece, never as filler): `time`, `simplicity`, `craft`, `sacred`.
- **Anchor references** (proximity = signal of fit): Patagonia (primary — rootedness, place, values-beyond-profit), Apple (careful innovation, simplicity, restraint as confidence), Anthropic (thoughtfulness, considered moves).
- **Anti-anchors** (proximity = failure signal): Elon Musk personal brand, Sam Altman / OpenAI marketing, parts of NVIDIA, parts of Microsoft. Never name-drop, never adopt their stylistic patterns.

## Language

- **Primary:** English.
- **Secondary:** German (EN → DE cultural adaptation, du-form, DACH market references).
- **Tertiary:** Dutch (NL for personal/NL network, "Kees" register, je/jij form, sign off as "Kees").
- All translation is cultural adaptation, never literal. Flag if a reference won't land.

## Visual

- **Palette (botanical, locked):**
  - Paper bone — `#F4EFE3` / `oklch(0.97 0.012 80)` — background, ~70% of every surface.
  - Forest moss — `#2C4A38` / `oklch(0.32 0.06 155)` — wordmarks, key links, drenched grounds.
  - Pine ink — `#1F2E26` / `oklch(0.30 0.02 145)` — body text.
  - Weathered ochre — `#B8884A` / `oklch(0.68 0.10 80)` — accent ≤5%: links, marks, hairlines, drift words.
  - Soft moss — `#C7CFB8` / `oklch(0.84 0.02 130)` — hairlines and rules only.
- **Type:** Vollkorn (variable, free, German "wholegrain"). Weights 400–900, italic + roman. Hierarchy via weight + size, not optical-size. No all-caps anywhere.
- **Photography:** Candid, natural light, Berlin and Brandenburg textures. Kitchen tables, notebooks, walks with Sien and Fimme.
- **Image generation:** All Casey-brand images route through OpenAI gpt-image-2 via Bildsprache. Identity pack at `/data/identity/casey/` carries reference images for Casey, Sien, and Fimme.
- **Never:** Chrome / lens-flare / neon / generic AI gradient mesh. Stock photos. Corporate blue. Tech-bro energy.

## Wordmark

- **Casey** in Vollkorn 800 at 32px, forest moss.
- Italic ochre kicker beneath at 13px: ***(also: Kees.)*** — Dutch/English readable, German colon-disambiguator.

## Registers

The shared voice above applies to all output. Register selects the *intent*:

### personal — recognition surface

> *Who Casey is.* casey.berlin lives here. Manifesto-adjacent. Vulnerable. Slow.

- **Intent signals:** "I believe in...", quiet confession, scene drop, kitchen-table moments, walks-with-the-dogs framing, slow-correspondence tone ("I read mail on Tuesday afternoons").
- **Opening preference:** scene drop or quiet confession ("Some days I feel like I'm on a speedboat.").
- **Closing preference:** reflective question or quiet landing.
- **Vocabulary tilt:** more sensory, more first-person verbs, more parentheticals as self-aware asides.
- **Hashtags:** sparing — manifesto-adjacent posts often have none.
- **Platforms:** reflection, blog, manifesto-style longform, LinkedIn-personal-stamp, Tuesday-afternoon emails.

### professional — verification surface

> *What Casey ships.* cdit-works.de lives here. Workshop voice. Direct. Concrete.

- **Intent signals:** "Here's what I shipped...", "The short version:", problem → insight → approach → outcome, real client examples (when permission granted), Praxiswissen frame.
- **Opening preference:** provocation or familiar reference recontextualized ("Fast, cheap, or good — pick two…" — but rendered as "Fast, cheap, or good. Pick two." per the no-em-dash rule).
- **Closing preference:** reframed mantra or one-line takeaway. No CTA; the work itself is the offer.
- **Vocabulary tilt:** more concrete nouns, more named tools, more specific numbers. Same load-bearing words, used sparingly.
- **Hashtags:** mix EN+DE, no umlauts (`#Fuehrung` not `#Führung`), 3–5 per post.
- **Platforms:** linkedin-post (workshop frame), linkedin-article, blog (techfeed/Praxiswissen), proposal, newsletter.

### Yorizon — separate context, not a register

Yorizon is a **fully isolated brand**, not a register on `casey`. Yorizon uses "we" voice, has its own voice DNA in `data/brands/yorizon.md`, and shares zero palette tokens, anchor references, or load-bearing words with `casey`. The `register` argument MUST NOT be used with `brand="yorizon"`.

## Anti-patterns (in addition to general voice DNA AI tells)

- "Excited to announce…" — never.
- "In today's fast-paced…" — never.
- "Just" used dismissively — cut.
- Stacked adjectives — pick the one that does the most work.
- Clickbait promises ("the secret to…", "what nobody tells you…") — never.
- AI hype framing ("game-changer", "revolutionary", "disrupt") — never.
- "Leverage" as a verb — never. Use "use".

## Closers (reminder, register-tilted)

- Personal: reflective question, quiet image, sometimes a rainbow emoji.
- Professional: reframed mantra or one-line takeaway. No CTA.
