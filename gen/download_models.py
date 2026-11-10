"""download_models.py : every model weight the pipeline used, fetched from the Hugging Face Hub into gen/models/.
Written for this export. It consolidates dl.py and the downloads that were run inline during the session.
Run from gen/ with the first virtual environment:  ./venv/bin/python download_models.py   (about 7.1 GB)
The speech models are fetched by their own packages on first use (docs/12, docs/13, docs/14)."""
from huggingface_hub import snapshot_download, hf_hub_download
# Stable Diffusion 1.5 fine-tune used for every still and every inpainted variant
snapshot_download("SG161222/Realistic_Vision_V5.1_noVAE", local_dir="models/rv51",
                  allow_patterns=["model_index.json", "scheduler/*", "text_encoder/*", "tokenizer/*", "unet/*", "vae/*"])
snapshot_download("stabilityai/sd-vae-ft-mse", local_dir="models/vae", allow_patterns=["config.json", "diffusion_pytorch_model.safetensors"])
# speed-up LoRAs: LCM was used only for the first benchmark, Hyper-SD was downloaded and never used
hf_hub_download("latent-consistency/lcm-lora-sdv1-5", "pytorch_lora_weights.safetensors", local_dir="models/lcm")
hf_hub_download("ByteDance/Hyper-SD", "Hyper-SD15-8steps-lora.safetensors", local_dir="models/hyper")
# face landmarks (OpenCV YuNet)
hf_hub_download("opencv/face_detection_yunet", "face_detection_yunet_2023mar.onnx", local_dir="models/yunet")
# person matting: MODNet was the first test, BiRefNet-portrait is what the cut-outs use (both ONNX, weights only)
hf_hub_download("Xenova/modnet", "onnx/model.onnx", local_dir="models/modnet")
hf_hub_download("onnx-community/BiRefNet-portrait-ONNX", "onnx/model.onnx", local_dir="models/birefnet_onnx")
# face re-posing (LivePortrait, ONNX export): only these six files; the repository's .dll/.so/.whl binaries were not fetched
for f in ["appearance_feature_extractor.onnx", "motion_extractor.onnx", "stitching.onnx", "stitching_lip.onnx", "stitching_eye.onnx", "warping_spade.onnx"]:
    hf_hub_download("warmshao/FasterLivePortrait", "liveportrait_onnx/" + f, local_dir="models/lp")
# the lip reference (request 10) and the face parser behind the body and hair maps (request 11): ONNX weights only, 0.5 GB
for f in ["wav2lip_96.onnx", "wav2lip_gan_96.onnx", "2dfan4.onnx"]: hf_hub_download("facefusion/models-3.0.0", f, local_dir="models/w2l")
hf_hub_download("facefusion/models-3.0.0", "bisenet_resnet_34.onnx", local_dir="models/parse")
# Not downloaded here: ZhengPeng7/BiRefNet (PyTorch). It was fetched during the session, but running it needs the
# repository's own Python code (trust_remote_code), which the session's permission check refused. See docs/09.
print("done")
