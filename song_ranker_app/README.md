# Song Score Cards — Transparent PNG Exporter

This Streamlit app turns a CSV of song scores into per-song transparent PNG "cards" like your example:

- Title on top, artist below.
- Left/right rails show each person's avatar + score chip.
- Highest score is **green**, lowest is **red**.
- If the person is the song **Submitter**, their chip shows a yellow **N**.
- Pick one **favorite** per person; a subtle star appears behind that person's chip on their favorite song.
- Optional **Average** column; if missing, it's computed from the scores.
- Export **individual PNGs** (transparent) or a **ZIP of all**.

## CSV format

`Submitter,Song,Artist,Average(optional),<Person1>,<Person2>,...`

Example:
```csv
Submitter,Song,Artist,Average,Nick,Jiho,Desmond,Jeff
Desmond,Give It To Me Baby,Rick James,7.00,8,9.9,10,7
Jiho,Yesterday,Atmosphere,6.98,9,10,9,6
```

Names in the score columns define the people list and should match avatar filenames where possible.

## Avatars

Upload a **ZIP** with avatar images. Filenames (without extension) should match people names (case-insensitive), e.g. `Nick.png`, `Jiho.jpg`. If a person's avatar is missing, a gray placeholder is used.

## Run locally

```bash
cd song_ranker_app
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown in your terminal.
