# Vintage: how to actually use it

`VINTAGE_WALKTHROUGH.md` is the architecture — routes, files, where the chain
stops. This is the other thing: what you click, in order, and what you should
see happen.

Everything here is on `studio.shirtfaced.wtf`, under **Research** and
**Evidence** in the top nav.

---

## Evidence — finding what to work from

3,639 cached listings, 11,544 images, from two collectors: eBay sold listings
and a design archive gathered from vintage resellers and collector communities.

Search by title, or filter by brand, era or tradition. **Each option shows its
own count**, so `1990s (939)` tells you the size of what you are about to pick
before you pick it. 233 records carry no era or tradition at all — those are
newer eBay agent records whose titles were not kept.

A card shows its brand (or a dash where the source never said one), the title,
era, tradition and image count, and a link to the original listing.

## Research — turning evidence into design prompts

### 1. Choose the evidence

Pick an era and a tradition, or leave both as All. Set **Images per run** —
1 to 24, default 16. Selection is breadth-first: the first image of every
listing before the second of any, so a run sees as many different pieces as it
can rather than one piece from many angles.

### 2. Prepare, don't spend

**Prepare manual run — no API cost** selects the evidence and stops. No model
is called and nothing is billed.

You get the images as thumbnails and the two prompts, each with a Copy button.

*(**Run both passes (billed)** does the same selection and then calls the API
itself. It works, and it charges an API key that bills separately from the
OpenAI, Gemini and Anthropic subscriptions already being paid for. It is there
for when that trade is worth it, not as the default.)*

### 3. Run the passes yourself

1. Save the images — right-click, or long-press on a phone. They deliberately
   do not open in a new tab: Chrome and Edge both block that, and a blocked tab
   loses everything prepared on the screen.
2. Copy **Pass 1** and send it with the images to ChatGPT or Gemini.
3. Send **Pass 2** to the same chat to deepen the same ten concepts.

The prompt asks for JSON explicitly, because a chat window has no schema
forcing the shape the way the API path does.

### 4. Import

Paste the JSON into the box and press **Import concepts**. Either ten cards
appear, or a red message under the button says exactly what was wrong:

| Message | Meaning |
|---|---|
| That is not valid JSON | prose came back, or the copy was partial |
| must return exactly 10 concepts | fewer or more than ten |
| must be numbered 1 through 10 in order | numbering skipped or reordered |
| missing the required POD-ready phrase | a prompt lost the print suffix |

Nothing is written unless it passes. The same validator runs on API output, so
work done in a chat window is held to the same standard.

## Reviewing

Each card carries the number, title, the idea, and the generation prompt in an
editable box with its own Copy button.

- **Approve** / **Reject** — records a decision.
- **Save edit** — keeps your version of the prompt.

Approving reveals a design-concept picker and **Send to design pipeline**.
Clicking it shows **Attempt N created** — a real `DesignAttempt` row against
that concept.

## What happens after that

Nothing automatic, on purpose.

The attempt sits in `PLANNED`. No image is generated, because generating one
through an API bills a second time for capability the subscriptions already
cover. Take the prompt, make the image where you already make images, then:

```
upload it to the attempt  →  submit  →  decide  →  approve
                          →  Print places it on a garment
```

That manual hop is the cheap path, not a defect. See
`VINTAGE_WALKTHROUGH.md` §7 for why, and §8 for the one thing it costs — the
evidence images inform the *words* but never reach the image generator, which
is why output tends toward competent modern skate art rather than 1991.

## When something looks broken

`python scripts/smoke_vintage.py` walks the chain against production and names
the broken link. It runs automatically as the last step of every deploy, so a
green deploy now means the chain answered, not merely that files copied.

It checks the server. It cannot see a React component throwing, so a blank
screen is still worth reporting.
