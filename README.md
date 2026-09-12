# AL NextGen Toastmasters — Personal VPPR Flyer Generator

A small Streamlit + Pillow application for generating the weekly club flyer from structured meeting details and member photos.

## What it does

- 1080 × 1350 flyer output
- Two presets:
  - Key Roles: TMOD / General Evaluator / TTM
  - Supporting Roles: Timer / Ah-counter / Grammarian
- Automatic photo crop + rounded corners
- Automatic text sizing
- Meeting number/date/time/venue
- Theme, Word of the Day, Idiom of the Day
- Reusable club logo
- Reusable Teams QR block
- PNG and PDF download

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Folder structure

```text
vppr_flyer_generator/
├── app.py
├── requirements.txt
├── README.md
└── assets/
    ├── default_logo.png
    └── default_teams_qr.png
```

## Important: replacing the default assets

The supplied sample flyer was used only to create the initial reusable logo and Teams block.

If the Teams meeting/QR changes, upload the new QR block in the app or replace:

`assets/default_teams_qr.png`

If the club branding changes, replace:

`assets/default_logo.png`

## Matching your Canva design more precisely

The current version recreates the layout using Pillow so it works without Canva.

If you want pixel-level matching later, the next upgrade would be to create a clean blank template/background from your Canva design and have the program fill only the dynamic fields/photos.

## Fonts

The app looks for Montserrat if you put these files into `assets/`:

- Montserrat-Regular.ttf
- Montserrat-SemiBold.ttf
- Montserrat-Bold.ttf
- Montserrat-Italic.ttf
- Montserrat-BoldItalic.ttf

If they are not present, the app falls back to DejaVu Sans.

## Weekly workflow

1. Open the app.
2. Enter meeting details.
3. Choose Key Roles or Supporting Roles.
4. Enter three names.
5. Upload three photos.
6. Click Generate Flyer.
7. Download PNG/PDF.
