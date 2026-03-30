# Brand Detection Rules

## Override Tags
Manual override always wins. Use `@tag` in prompt:
`@casey.berlin` · `@cdit` · `@storykeep` · `@nah` · `@yorizon`

## Auto-Detection Signals

| Context | Signals |
|---------|---------|
| casey.berlin | "manifesto", "personal", "casey.berlin", "reflection", "newsletter", "writings", essay topics (creativity, AI philosophy, identity, making) |
| cdit-works.de | "CDI-" prefix, "client", "Sprechstunde", "Digitale Sprechstunde", "Mittelstand", "Praxiswissen", "proposal", "angebot", consulting/development |
| StoryKeep | "Piet", "Jamie", "museum", "Sugahara", "StoryKeep", "exhibition", "rooms", "family" |
| Nah? | "Nah", "community", "social network", "Mastodon", "fediverse", "privacy", "local", "Dunbar" |
| Yorizon | "Nexus", "Yorizon", "translation", "Impartner", "PO", "Product Owner", "localization", "TMS" |

## Disambiguation

- If topic involves first-person experience, emotion, or philosophical reframing AND no client/commercial signals → prefer **casey.berlin**
- If content could belong to multiple contexts → prefer the **more specific** context
- **Low confidence (no strong signals):** ASK the user — do NOT default silently. Prompt: "I don't have a clear context signal. Is this @casey.berlin or @cdit?"
- Explicit `@tag` → skip confirmation and proceed directly

## Context Bleed Prevention

- Never mix visual languages across contexts in a single piece
- Yorizon content MUST be scanned for forbidden vocabulary before output (see `shared/brands/yorizon.md`)
- If Yorizon content drifts toward CDiT territory → block and explain
