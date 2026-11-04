Put these font files here (all are free, open-licensed):

| File | Used by | Where to get it |
|---|---|---|
| `Inter-Bold.otf`, `Inter-Medium.otf`, `Inter-SemiBold.otf` | all on-screen text | Inter (SIL Open Font License): https://rsms.me/inter/ |
| `texgyrepagella-bolditalic.otf` | the π outline in `fourier.py` | TeX Gyre Pagella (GUST Font License): https://www.gust.org.pl/projects/e-foundry/tex-gyre/pagella |
| `NotoColorEmoji.ttf` | car and goat icons in `monty.py` | Noto Color Emoji (SIL Open Font License): https://github.com/googlefonts/noto-emoji |

The scripts look here first, then in the usual system font folders.
`brach.py`, `bday.py` and `monty.py` also ask cairo for a font named "Inter", so install Inter system-wide too (double-click the .otf files on macOS).
