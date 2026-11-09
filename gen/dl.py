from huggingface_hub import snapshot_download, hf_hub_download
import time
t=time.time()
p=snapshot_download("SG161222/Realistic_Vision_V5.1_noVAE", local_dir="models/rv51",
    allow_patterns=["model_index.json","scheduler/*","text_encoder/*","tokenizer/*","unet/*","vae/*"])
print("rv", time.time()-t)
hf_hub_download("latent-consistency/lcm-lora-sdv1-5","pytorch_lora_weights.safetensors", local_dir="models/lcm")
snapshot_download("stabilityai/sd-vae-ft-mse", local_dir="models/vae", allow_patterns=["config.json","diffusion_pytorch_model.safetensors"])
hf_hub_download("ByteDance/Hyper-SD","Hyper-SD15-8steps-lora.safetensors", local_dir="models/hyper")
print("done", time.time()-t)
