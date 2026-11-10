# The television and the page

Source: [`src/page.html`](../src/page.html). It has not changed much since the first request; the news channel is the
part that was rewritten. The marker `/*NEWS*/` in the script is where `build.py` inserts `src/news.js`.

## How a frame is made

1. A hidden 1024×576 Canvas 2D (`scr`) is the television picture. The current channel draws one frame into it.
2. That canvas is uploaded as a texture with `texImage2D`.
3. The room is drawn in WebGL: floor, console and set as boxes, then the picture as one textured rectangle.

There are no libraries. Matrices (`perspective`, `lookAt`, `mul`) are a dozen lines of arithmetic.

## The model

Dimensions are in metres and follow the 65-inch C4: a 1441 × 826 mm panel a few millimetres thick, an electronics housing
on the lower back, and a centred pedestal stand. Every solid is the same unit cube drawn with a centre, a size and a
colour, so there is one vertex buffer and one draw call per box.

| Part | Size (w × h × d) | Notes |
|---|---|---|
| OLED panel | 1.441 × 0.826 × 0.006 | near-black, glossy |
| Rear skin | 1.437 × 0.822 × 0.001 | slightly lighter so the back reads as a surface |
| Rear housing | 1.19 × 0.46 × 0.04 | lower back, plus a 0.02 taper strip above it |
| VESA plate | 0.30 × 0.20 | on the housing |
| Stand neck | 0.36 × 0.19 × 0.03 | aluminium grey |
| Stand plate | 0.475 × 0.012 × 0.23 | aluminium grey |
| Standby LED | 0.022 × 0.004 × 0.006 | under the panel, glows red when the set is off |
| Console | 2.0 × 0.42 × 0.44 body, 2.06 × 0.02 × 0.48 top, two feet, a door gap | top surface at 0.5 m, glossy |
| Floor | 18 × 18 | fades into the background with distance |

The picture is inset 7 mm from the panel edge and sits 0.6 mm in front of it.

## Shaders

**Boxes.** Two directional lights with Lambert shading, a Blinn-Phong highlight, and light spilled by the picture. For
the spill, each surface point finds the nearest point on the screen rectangle, treats it as the emitter, and receives the
picture's average colour scaled by the angle to the surface, by how far in front of the screen the point lies, and by
distance. Colour then fades to the background between 2.2 m and 7.5 m from the centre.

**Reflection.** Surfaces marked glossy (the console top and the stand plate) also reflect the picture. For a fragment
facing up, the shader reflects the view ray, finds where it meets the screen plane, and if that lands on the picture adds
the texture there, read from a blurrier mip level and faded the further the ray travelled. The console is shallow and the
picture starts 7 cm above it, so the reflection shows only from a raised camera.

**Picture.** The texture, plus a glass sheen that grows at grazing angles. An OLED has true black, so nothing is added
when the picture is dark.

**Average colour.** Every fourth frame the picture is drawn into a 4×4 canvas and read back; the mean, smoothed, is the
spill colour. This is why the console top changes colour with the programme.

**Filtering.** With WebGL 2 the picture texture gets mipmaps every frame and up to 8× anisotropic filtering, which keeps
photographs and small type clean when the set is small or seen at an angle. With WebGL 1 it falls back to plain linear
filtering, because that version cannot mipmap a 1024×576 texture.

## Camera and controls

An orbit camera looks at a point 0.9 m up. It drifts slowly until the first touch. Drag orbits (pitch limited to
−0.12 to 1.35 radians so the camera stays above the floor), wheel or pinch zooms between 1.1 m and 6.5 m. On portrait
screens the distance is multiplied by `0.92 / aspect` so the whole set stays in frame.

The remote is ordinary HTML over the canvas: power, channel down, the channel name, channel up, sound, volume down,
volume up. Keys: arrows change channel, `1`–`5` jump, `P` toggles power, `M` toggles sound, `-` and `=` change the
volume. On phones the volume buttons are hidden. Turning sound on or changing the volume shows a bar on the TV picture.

## Channels

| # | Name | What it draws |
|---|---|---|
| 1 | DevOps Tonight | The news show. See [07](07-runtime-compositing.md) |
| 2 | Plasma | A 160×90 per-pixel sine plasma, scaled up |
| 3 | Screensaver | The show's logo bouncing off the edges, counting restarts and corner hits |
| 4 | Deploy Log | A star field with a scrolling pipeline log |
| 5 | Test Card | Colour bars with `tv 1/1 Running` and a live clock |

Changing channel shows 0.32 seconds of static and a channel banner for 2.6 seconds. Power-on fades in over 0.8 seconds.
Tuning to channel 1 restarts the bulletin from its titles.

If a channel's draw function throws, the frame loop catches it, resets the canvas and shows "Picture unavailable on this
channel", so one bad frame cannot stop the set.

## Things added to this file after the first version

- WebGL 2 with mipmaps and anisotropy (request 4).
- The try/catch around channel drawing (request 4).
- A phone layout for the remote, so the channel name does not wrap (request 4).
- The standing line under the controls: "Channel 1 is satire. Its presenters and locations are AI-generated stills, not
  real people or places." (request 4).
- The header comment describing where the pictures come from (requests 4 and 6).
- Sound: the buttons, keys and volume bar, and the call to the sound engine each frame (request 8). The engine itself is
  [`src/sound.js`](../src/sound.js), described in [12](12-voices-and-sound.md).
- The reflection, and a fix to the console: its body and top slab had coplanar top faces that flickered against each other
  as a stepped pattern. The body now stops under the slab (request 8).
- The picture is uploaded to the GPU before the boxes are drawn, because the boxes now read it (request 8).
