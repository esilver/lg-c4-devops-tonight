import torch, time, os
from diffusers import (StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, StableDiffusionInpaintPipeline,
                       LCMScheduler, AutoencoderKL, DPMSolverMultistepScheduler)
from PIL import Image
torch.set_num_threads(4)
NEG = ("cartoon, illustration, painting, drawing, 3d render, cgi, anime, doll, plastic skin, airbrushed, deformed, disfigured, "
       "extra fingers, bad hands, text, watermark, logo, caption, letters, subtitles, blurry face, cross-eyed, side view, profile, looking away, tilted head, nsfw, nude")

def load(mode="lcm", dtype=torch.bfloat16):
    vae = AutoencoderKL.from_pretrained("models/vae")
    pipe = StableDiffusionPipeline.from_pretrained("models/rv51", vae=vae, safety_checker=None, feature_extractor=None, requires_safety_checker=False)
    if mode == "lcm":
        pipe.load_lora_weights("models/lcm", weight_name="pytorch_lora_weights.safetensors"); pipe.fuse_lora(); pipe.unload_lora_weights()
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    elif mode == "hyper":
        pipe.load_lora_weights("models/hyper", weight_name="Hyper-SD15-8steps-lora.safetensors"); pipe.fuse_lora(); pipe.unload_lora_weights()
        from diffusers import DDIMScheduler
        pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
    else:
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True, algorithm_type="dpmsolver++", solver_order=2)
    pipe.unet.to(dtype).to(memory_format=torch.channels_last); pipe.text_encoder.to(dtype)
    pipe.set_progress_bar_config(disable=True)
    return pipe

def decode(pipe, latents):
    with torch.no_grad():
        img = pipe.vae.decode(latents.float() / pipe.vae.config.scaling_factor).sample
    img = (img / 2 + 0.5).clamp(0, 1)[0].permute(1, 2, 0).numpy()
    return Image.fromarray((img * 255).round().astype("uint8"))

def encode(pipe, pil, gen=None):
    import numpy as np
    x = torch.from_numpy(np.asarray(pil.convert("RGB")).astype("float32") / 127.5 - 1).permute(2, 0, 1)[None]
    with torch.no_grad():
        return pipe.vae.encode(x).latent_dist.mode() * pipe.vae.config.scaling_factor

def t2i(pipe, prompt, seed, w=768, h=432, steps=6, cfg=1.5, neg=NEG):
    g = torch.Generator().manual_seed(seed)
    with torch.no_grad():
        lat = pipe(prompt, negative_prompt=neg, width=w, height=h, num_inference_steps=steps, guidance_scale=cfg, generator=g, output_type="latent").images
    return decode(pipe, lat)

# ---- manual DDIM img2img / inpaint (keeps the VAE in fp32 and the UNet in bf16) ----
import numpy as np

def embed(pipe, prompt, neg=NEG):
    with torch.no_grad():
        pos, ng = pipe.encode_prompt(prompt, "cpu", 1, True, negative_prompt=neg)
    return pos, ng

def ddim(pipe, prompt, init_lat, strength=0.35, steps=20, cfg=5.0, seed=0, mask=None, neg=NEG):
    """init_lat: fp32 latents. mask: (1,1,h,w) float, 1 = repaint, 0 = keep (latent resolution)."""
    ac = pipe.scheduler.alphas_cumprod.float()
    ts = (np.round(np.linspace(1000, 0, steps + 1))[:-1] - 1).astype(int)
    n = max(1, int(round(steps * strength))); ts = ts[steps - n:]
    g = torch.Generator().manual_seed(seed); noise = torch.randn(init_lat.shape, generator=g)
    a0 = ac[ts[0]]; x = a0.sqrt() * init_lat + (1 - a0).sqrt() * noise
    pos, ng = embed(pipe, prompt, neg); ctx = torch.cat([ng, pos])
    dt = pipe.unet.dtype
    for i, t in enumerate(ts):
        with torch.no_grad():
            e = pipe.unet(torch.cat([x, x]).to(dt).contiguous(memory_format=torch.channels_last), int(t), encoder_hidden_states=ctx).sample.float()
        eu, ec = e.chunk(2); e = eu + cfg * (ec - eu)
        a = ac[t]; x0 = (x - (1 - a).sqrt() * e) / a.sqrt()
        ap = ac[ts[i + 1]] if i + 1 < len(ts) else torch.tensor(1.0)
        x = ap.sqrt() * x0 + (1 - ap).sqrt() * e
        if mask is not None:
            known = ap.sqrt() * init_lat + (1 - ap).sqrt() * noise
            x = mask * x + (1 - mask) * known
    return x

def img2img(pipe, prompt, pil, **kw):
    return decode(pipe, ddim(pipe, prompt, encode(pipe, pil), **kw))

def inpaint(pipe, prompt, pil, mask_pil, **kw):
    """mask_pil: 'L' image same size as pil, white = repaint."""
    lat = encode(pipe, pil)
    m = mask_pil.convert("L").resize((lat.shape[3], lat.shape[2]), Image.BILINEAR)
    m = torch.from_numpy(np.asarray(m).astype("float32") / 255.0)[None, None]
    return decode(pipe, ddim(pipe, prompt, lat, mask=m, **kw))
