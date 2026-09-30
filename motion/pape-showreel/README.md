# PAPE — showreel motion design (20 s)

Vidéo 1920×1080, 60 i/s, avec bande-son, entièrement générée par du code.

- `index.html` : l'animation (Canvas 2D). Ouvre-la dans un navigateur pour l'aperçu en boucle.
- `audio.py` : bande-son synthétisée à 120 BPM, calée sur les coupes → `soundtrack.wav`.
- `render.mjs` : capture chaque image avec Playwright et encode avec ffmpeg → `pape-showreel.mp4`.

```bash
pip install numpy
python3 audio.py
node render.mjs                      # vidéo complète
node render.mjs --stills 2.5,10,18   # images de contrôle
```
