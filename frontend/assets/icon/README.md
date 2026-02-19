# App Icon Assets

## Files Needed

| File | Size | Description |
|---|---|---|
| `app_icon.png` | 1024×1024 | Full app icon (export from SVG) |
| `app_icon_foreground.png` | 1024×1024 | Android adaptive icon foreground (book+arrow on transparent bg, content within 66% safe zone) |
| `app_icon.svg` | — | Source vector (included) |

## How to Generate

1. Open `app_icon.svg` in Figma, Illustrator, or Inkscape
2. Refine the design as needed
3. Export `app_icon.png` at 1024×1024 (no transparency for iOS)
4. Export `app_icon_foreground.png` at 1024×1024 with transparent background (for Android adaptive icon)
5. Run: `dart run flutter_launcher_icons -f flutter_launcher_icons.yaml`

## Design Spec

- **Background:** Linear gradient #4A00E0 → #8E2DE2 (indigo to purple)
- **Foreground:** White open book with a curved swipe arrow beneath
- **Style:** Minimal, modern, rounded corners (applied by OS)
- **Safe zone:** Keep key elements within the center 66% for Android adaptive icon cropping
