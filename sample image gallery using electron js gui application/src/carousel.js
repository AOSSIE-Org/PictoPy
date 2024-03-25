const carousel_btns = document.querySelectorAll("[data-carousel-btn]");
const info_btn = document.querySelector(".popup-image-container .info .btn-info");
const carousel_info = document.querySelector(".popup-image-container .info");
const carousel_info_text = document.querySelector(".popup-image-container .info .info-text p");

carousel_btns.forEach(btn => {
  btn.addEventListener("click", () =>{
    const offset = btn.getAttribute("data-carousel-btn") === "next" ? 1 : -1;
    const activeSlide = gallery_container.querySelector("[data-active]");
    let newIndex = [...gallery_container.children].indexOf(activeSlide) + offset;
    if (newIndex < 0) newIndex = gallery_container.children.length - 1;
    if (newIndex >= gallery_container.children.length) newIndex = 0;

    const newActiveitem = gallery_container.children[newIndex];
    newActiveitem.dataset.active = true;
    delete activeSlide.dataset.active;

    const newActiveimg = newActiveitem.querySelector("img");
    setPopupData(newActiveimg, newIndex);

  });
});

info_btn.addEventListener("click", () => {
  carousel_info.toggleAttribute("data-active-info");
});