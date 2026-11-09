# HISTORICAL. Placeholder assets in the *first* asset format (one inpainted mouth sprite per shape), used once to
# exercise the page code before the real pipeline had finished. The current page expects the pose-grid format written by
# gen/lpexport.py, so this output no longer loads. Run from the repository root. In the original session it wrote
# ../assets.json; it now writes ../assets_fake.json so it cannot overwrite the real bundle.
import sys, json, base64, io
import os; os.chdir('gen'); sys.path.insert(0, os.getcwd())
from facelib import *
def uri(im, fmt='JPEG', **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()
A = dict(img={}, cast={})
src = dict(paige='out/base_paige_21.png', cy='out/base_cy_22.png', dee='out/base_dee_22.png', sunny='out/base_sunny_23.png', mel='out/base_mel_21.png')
for i, (k, f) in enumerate(src.items()):
    im = Image.open(f).convert('RGB').resize((1024, 576), Image.LANCZOS); lm = landmarks(im)
    eL, eR = np.array(lm['eyeL']), np.array(lm['eyeR']); mL, mR = np.array(lm['mouthL']), np.array(lm['mouthR']); iod = float(np.linalg.norm(eR - eL)); ec = (eL + eR) / 2; mc = (mL + mR) / 2
    mb = [int(mc[0] - 0.7 * iod), int(mc[1] - 0.3 * iod), int(1.4 * iod), int(0.9 * iod)]
    spr = Image.new('RGBA', (mb[2], mb[3]), (40, 10, 10, 0)); d = ImageDraw.Draw(spr); d.ellipse([mb[2] * .25, mb[3] * .2, mb[2] * .75, mb[3] * .7], fill=(60, 15, 15, 255))
    eb = [int(eL[0] - 0.4 * iod), int(ec[1] - 0.25 * iod), int(1.8 * iod), int(0.5 * iod)]
    bl = im.crop((eb[0], eb[1] - 6, eb[0] + eb[2], eb[1] - 6 + eb[3])).convert('RGBA')
    A['cast'][k] = dict(bg=uri(im, quality=85), fg=uri(im, 'WEBP', quality=85), seed=1.0 + i * 1.7, face=dict(cx=float(ec[0]), cy=float(ec[1] + 0.45 * iod), iod=iod),
        mouth=dict(x=mb[0], y=mb[1], map=[-1, 0, 0, 0, 0], frames=[uri(spr, 'WEBP', lossless=True)]), blink=dict(x=eb[0], y=eb[1], src=uri(bl, 'WEBP', quality=85)))
for k, f in dict(studio='out/bench_dpm_bf16_25_12.jpg', servers='out/base_dee_21.png', dcext='out/base_dee_23.png', office='out/base_mel_22.png', paged='out/base_mel_23.png', sat='out/base_sunny_22.png').items():
    A['img'][k] = uri(Image.open(f).convert('RGB').resize((1024, 576), Image.LANCZOS), quality=85)
json.dump(A, open('../assets_fake.json', 'w')); print('ok')
