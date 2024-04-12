import requests  # type:ignore
import sys
import tempfile
from operator import itemgetter
from pathlib import Path
from typing import Callable, List, Tuple, Union

import streamlit as st
from streamlit.uploaded_file_manager import UploadedFile
import torch
import torchvision.transforms as transforms
from facenet_pytorch import MTCNN, InceptionResnetV1, extract_face
from fastai.vision.core import PILImage
from PIL import Image, ImageDraw, ImageFont
from torch import Tensor

PathLike = Union[Path, str]

pil2t = transforms.ToTensor()
t2pil = transforms.ToPILImage()

st.set_page_config(page_title="ML deployment, by unpackAI", page_icon="🖼️")
st.image("https://unpackai.github.io/unpackai_logo.svg")
st.title("Facial Identification")
st.write("### one-shot inference")
st.write("💉 *by Jeff* 🔫")
st.write("---")


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Create an inception resnet (in eval mode for inference)
@st.cache(allow_output_mutation=True)
def get_resnet():
    return InceptionResnetV1(pretrained="vggface2").eval().to(device)


resnet = get_resnet()


@st.cache
def get_image(img: PathLike) -> PILImage:
    """Get picture from either a path or URL"""
    if str(img).startswith("http"):
        with tempfile.TemporaryDirectory() as tmpdirname:
            dest = Path(tmpdirname) / str(img).split("?")[0].rpartition("/")[-1]
            with requests.get(str(img)) as resp:
                resp.raise_for_status()
                dest.write_bytes(resp.content)

            return PILImage.create(dest)
    else:
        return PILImage.create(img)


def img_2_embedding(img_path: Union[PathLike, UploadedFile]) -> Tensor:
    """Calculate the embedding of a picture"""
    resnet.classify = False
    # We need to feed with a Tensor of pixels => we need to transform first
    # We use `unsqueeze` to add batch dimension
    img = pil2t(Image.open(img_path))
    return resnet(img.unsqueeze(0).to(device))


DistFunc = Callable[[Tensor, Tensor], Union[float, Tensor]]
ListReferences = List[Union[Path, UploadedFile]]


def get_img_stem(img: Union[Path, UploadedFile]) -> str:
    if isinstance(img, UploadedFile):
        img = Path(img.name)
    return img.stem


class FacialRecognizer:
    # @st.cache(allow_output_mutation=True)
    def __init__(
        self, references: ListReferences, distance_func: DistFunc = torch.dist
    ):
        self.distance = distance_func
        self.references = {
            get_img_stem(img): img_2_embedding(img) for img in references
        }

    def _embedding_2_person(
        self, emb: Tensor, alpha: float = 0.2, threshold: float = 1.2
    ) -> Tuple[str, float]:
        if not self.references:
            raise ValueError("No reference images loaded")

        dist = {p: self.distance(emb, img) for p, img in self.references.items()}
        (p1, min_1), (_, min_2) = sorted(dist.items(), key=itemgetter(1))[:2]
        if min_1 > threshold:
            return "??", threshold

        triplet_dist = float(min_1 - min_2 + alpha)
        if triplet_dist <= 0:
            person = p1
        elif triplet_dist <= alpha:
            person = f"~{p1}"
        else:
            person = f"?? ({p1}?)"
        return person, triplet_dist

    def get_person(self, img_path: PathLike, alpha: float = 0.2) -> Tuple[str, float]:
        """Return most likely person from an image path"""
        new_img = img_2_embedding(img_path)
        return self._embedding_2_person(new_img, alpha)

    def face_2_person(self, face: Tensor, alpha: float = 0.2) -> Tuple[str, float]:
        """Return most likely person from a face"""
        # We first need to embed the face for comparison
        new_img = resnet(face.unsqueeze(0).to(device))
        return self._embedding_2_person(new_img, alpha)


st.sidebar.header("References Images")
select_references = st.sidebar.radio(
    "Which references to choose", ["Friends", "Custom"]
)
if select_references == "Friends":
    st.sidebar.write(
        '*We are using one picture for each one of the "Friends": Ross, Rachel, etc.*'
    )
    reference_dir = Path(__file__).parent / "friends_reference"
    references = list(reference_dir.glob("*.jpg"))
else:
    st.sidebar.write(
        "Update one picture per person named after the person "
        "*(e.g. 'Ada.jpg' for person named Ada)*"
    )
    references = st.sidebar.file_uploader(
        "Upload reference pictures", accept_multiple_files=True
    )

recognizer = FacialRecognizer(references=references)
if references:
    st.sidebar.write(f"✔️🖼️ {len(references)} reference images found")
else:
    st.sidebar.write(f"❌🖼️ No reference image found")


# @st.cache()
def show_persons_in_photos(
    img: Image.Image,
    recognizer: FacialRecognizer,
    keep_all=True,
    show_score=False,
    min_face_size=20,
    threshold=0.8,
    ratio_face=0.02,
) -> Tuple[str, Image.Image]:
    """Crop face with MTCNN and return cropped & prewhitened image tensor"""
    mtcnn = MTCNN(
        image_size=160,
        margin=0,
        device=device,
        keep_all=keep_all,
        select_largest=True,
        min_face_size=min_face_size,
    )
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            boxes, probs = mtcnn.detect(img)
            if boxes is None or not boxes.size:
                return "No face", img
            img_draw = img.copy()
            draw = ImageDraw.Draw(img_draw)
            persons: List[str] = list()
            boxes_probs = sorted(zip(boxes, probs), key=lambda t: t[0][0])
            for i, (box, prob) in enumerate(boxes_probs, start=1):
                face = box.tolist()
                ratio_w = (face[2] - face[0]) / img.shape[0]
                ratio_h = (face[3] - face[1]) / img.shape[1]
                if min(ratio_w, ratio_h) < ratio_face:
                    continue
                if prob >= threshold:
                    # We need to save the picture and load it again
                    # ... because feeding a extract from the box did not seem to work
                    # ... or maybe it's because I did not understand how to do it
                    pic_path = Path(tmpdirname) / f"pic_{i}.jpg"
                    _ = extract_face(img, box, save_path=pic_path)
                    person, score = recognizer.get_person(pic_path)
                    persons.append(person)
                    draw.rectangle(face, width=5)
                    name_score = (
                        f"#{i}.{person}:{score:.2f}" if show_score else f"#{i}.{person}"
                    )

                    arial = Path(__file__).with_name("arial.ttf")
                    font = ImageFont.truetype(str(arial), 20)
                    draw.text(face, name_score, font=font, fill=(255, 255, 255, 255))

            found_persons = ", ".join(persons) if persons else "No face identified"
            return found_persons, img_draw

    # We want to remove mtcnn at the end to reduce memory usage
    finally:
        del mtcnn


@st.cache()
def pic_2_predictions(pic):
    img = get_image(pic)
    return show_persons_in_photos(img, recognizer=recognizer)


def display_prediction(pic):
    persons, img_annotation = pic_2_predictions(pic)
    col_img, col_pred = st.columns(2)
    col_img.image(img_annotation, caption=getattr(pic, "name", None))
    col_pred.write(f"### {persons}")


select = st.radio(
    "How to load pictures?", ["from files", "from samples of Friends", "from URL"]
)
st.write("---")

if select == "from URL":
    url = st.text_input("url")
    if url:
        display_prediction(url)

elif select == "from samples of Friends":
    pictures = sorted(Path(__file__).parent.glob("friends_samples/*.jpg"))
    for pic in pictures:
        display_prediction(pic)

else:
    pictures = st.file_uploader("Choose pictures", accept_multiple_files=True)
    for pic in pictures:  # type:ignore # this is an iterable
        display_prediction(pic)
