`
# AI Image Generation with Dreamshaper 8

`lykon/dreamshaper-8` is a fine-tuned Stable Diffusion model based on `runwayml/stable-diffusion-v1-5`. This version focuses on improving previous iterations and balances realism and anime-style generation. It may require some expertise to achieve photorealism or anime-style images, but it's quite versatile for both types.

## Features

- **Improved Speed and Quality**: Fine-tuned for faster and more efficient image generation with high-quality outputs.
- **Flexible Usage**: Suitable for both photorealism and anime-style generation.
- **Enhanced Lora Support**: Adds better support for Lora and style customization.
- **Customizable Generation**: Generate detailed images from text prompts using guidance mechanisms.

## Installation

Make sure to install the necessary dependencies to run the model:

```bash
pip install diffusers transformers accelerate
```

## Usage

To generate an image with the `lykon/dreamshaper-8` model, you can use the following code:

```python
from diffusers import AutoPipelineForText2Image, DEISMultistepScheduler
import torch

# Load the pre-trained model with 16-bit precision for faster inference
pipe = AutoPipelineForText2Image.from_pretrained('lykon/dreamshaper-8', torch_dtype=torch.float16, variant="fp16")

# Set the scheduler for multi-step inference
pipe.scheduler = DEISMultistepScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to("cuda")

# Define your prompt
prompt = "portrait photo of muscular bearded guy in a worn mech suit, light bokeh, intricate, steel metal, elegant, sharp focus, soft lighting, vibrant colors"

# Set the random seed for reproducibility
generator = torch.manual_seed(33)

# Generate the image with 25 inference steps
image = pipe(prompt, generator=generator, num_inference_steps=25).images[0]  

# Save the generated image
image.save("./image.png")
```

## Notes

- **Version 8**: This version improves upon what V7 started. While photorealism may be harder to achieve compared to realism-focused models, Dreamshaper 8 handles both photorealistic and anime styles effectively if you have the right expertise. Check the examples for better understanding.
- **Version 7**: Focuses on better Lora support, NSFW generation, and improved realism.
- **Version 6**: Adds more Lora support and style flexibility. It should handle direct generation at 1024 height better, but be cautious with it.
- **Version 5**: Best for photorealism with noise offset adjustments.
- **Version 4**: Excels at anime generation and booru tags. It can be trickier to control for caption-style generation, so consider using version 3.31 for those specific cases.
- **Version 3.31 and below**: Generally, improvements over previous versions in terms of control and output consistency.

## Inference API

The model is available for text-to-image generation through the Inference API. You can explore more examples and experiment with the model's capabilities through available spaces using `lykon/dreamshaper-8`.

## Examples

You can find more examples and code for various use cases on platforms like:

- **Krebzonide/SDXL-Turbo-With-Refiner**
- **hansyan/perflow-triposr**
- **Nymbo/image_gen_supaqueue**
- **Huage001/LinFusion-SD-v1.5**

Check out other exciting spaces and projects using `lykon/dreamshaper-8`.

## Model Tree

- **Adapters**: 2 models available.
- **Spaces Using Lykon/dreamshaper-8**: 30 projects are currently using the model for different applications.

---
`