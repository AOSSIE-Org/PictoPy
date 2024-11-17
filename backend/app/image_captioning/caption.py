from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration



def caption1(img):
    processor = BlipProcessor.from_pretrained("salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("salesforce/blip-image-captioning-base")

   
    img_input = Image.fromarray(img)
    inputs = processor(img_input, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_token=True)
    return caption