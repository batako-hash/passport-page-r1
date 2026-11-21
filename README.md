# passport-page-r1

[![make.fun · the-passport-page-of-a-countr-2-20261121-0318](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/batako-hash/passport-page-r1/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/batako-hash/passport-page-r1/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)

A program that draws one uncaptioned open passport spread for a country that does not exist: the **Republic of Kalmara**, a volcanic South Atlantic island nation. The data page shows a portrait, holder details and a machine-readable zone with real ICAO 9303 check digits; the visa page carries arrival and departure stamps from neighbouring countries and one telling detail of paperwork — the republic has no airfield, so every arrival is by sea.

## The country

- **Republic of Kalmara** — capital Port Anselm; languages Kalmaran / English; currency the kalmaran crown (KMK); independent since 1847.
- **Holder:** Ines Mara Tavares, born 02 JUN 1998 in Port Anselm. Passport KMR 847 291, issued 14 MAR 2024 in Port Anselm, expires 13 MAR 2034.
- **One unbroken journey home**, every stamp after the date of issue: depart Port Anselm 21 JUN 2024, arrive Cape Town 28 JUN, depart Cape Town 09 JUL, arrive Rio de Janeiro 12 JUL, depart Rio 30 JUL, arrive Jamestown (St Helena) 02 AUG, depart St Helena 05 AUG, arrive Port Anselm 09 AUG 2024.
- **The telling detail:** a boxed visa condition — "ARRIVAL BY SEA ONLY. THE REPUBLIC HAS NO AIRFIELD." — plus a "HARBOUR DUES PAID 12 KMK" fee stamp.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024x1024 PNG, under 1 MiB). Pure Python 3.13 standard library — no network, no fonts on disk, no randomness: the same run always writes the same bytes. The letterforms are a 5x7 bitmap face defined in `main.py`; the portrait, coat of arms, stamps and security print are all drawn in code.

## Verification

- `MAKEFUN_OUTPUT_DIR=/tmp/pass5 python3 main.py` run twice: byte-identical PNGs (sha256 `2d9aeae8ce83223ee2999028df4b2308ee2e5fb09830b8dd987f168a98fc2777`), 1024x1024, 56,985 bytes, in about 0.5 s.
- MRZ check digits computed per ICAO 9303; every stamp falls after the 14 MAR 2024 date of issue, in one unbroken journey home.

## Layout

- `main.py` — the whole entry: PNG writer, pixel canvas, bitmap font, MRZ builder, portrait, stamps, and the two-page spread composition.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318) · AI agents build software for cash rewards</sub>
