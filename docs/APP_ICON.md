# FuelLoc application icon

The blue tile combines a location pin with a fuel pump. The same artwork is used in the workspace header, browser app-window favicon, startup window, and Windows executable.

- `src/static/fuelloc-source.png`: original generated RGBA artwork, 1254 × 1254.
- `src/static/fuelloc-256.png`: 256 × 256 header asset.
- `src/static/fuelloc.ico`: Windows icon containing 16, 24, 32, 48, 64, 128, and 256 pixel images.

Created with the built-in image generation tool. The prompt was:

> Use case: logo-brand. Asset type: FuelLoc Windows desktop application icon, also used at 40 px in the app header. Create one finished square icon: a bold white location pin fused with a simple fuel pump silhouette, centered on a rich blue rounded-square tile matching #2563eb, with a restrained lighter-blue depth accent. Clean modern desktop icon, crisp large geometric shapes, excellent legibility at 16 and 32 pixels. The fuel pump and location pin should read as one coherent distinctive symbol. Transparent outside the rounded tile. No text, letters, numbers, mockup, multiple variants, surrounding scene, thin details, or watermark.

Only output resizing and ICO encoding were applied after generation, preserving alpha. To reproduce the exports with Pillow available in the build environment:

```python
from pathlib import Path
from PIL import Image

assets = Path('src/static')
image = Image.open(assets / 'fuelloc-source.png')
image.resize((256, 256), Image.Resampling.LANCZOS).save(assets / 'fuelloc-256.png')
image.save(assets / 'fuelloc.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
```

Pillow is an export tool, not a runtime requirement. `scripts/build.ps1` bundles the static assets and embeds the ICO in the EXE; its generated `FuelLoc.spec` retains these options. Windows may cache executable/taskbar icons; verify a newly extracted release folder when checking branding. The browser still owns the app window and its taskbar grouping.
