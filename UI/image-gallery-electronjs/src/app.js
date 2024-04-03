const gallery_container = document.querySelector(".gallery-container");
const carousel_container = document.querySelector(".popup-image-window");
const carousel_img = document.querySelector(".popup-image-container img");
const carousel_img_name = document.querySelector(".popup-image-container .text .img-name");
const carousel_img_size = document.querySelector(".popup-image-container .text .sm-text");
const carousel_position_cnt = document.querySelector(".popup-image-container .text .position-cnt");
const carousel_btn_close = document.querySelector(".popup-image-window span");
const btn_add = document.querySelector(".btn-add");
let dbImgGallery;
let modifyGalleryItem;

function imgsCard({idImg,imgName,imgPath,imgSize}) {
  return `
  <div class="menu-options-container">
  <ul class="menu-options">
    <button class="btn-options"><i class="bi bi-three-dots-vertical"></i></button>
    <li class="btn-edit" style="--i:0" data-bs-toggle="modal" data-bs-target="#editModal"><i class="bi bi-pencil"></i></li>
    <li class="btn-delete" style="--i:1"><i class="bi bi-trash3"></i></li>
  </ul>
  </div>

  <img src="${'../img/'+imgPath}" alt="${imgName}" data-id="${idImg}" loading="lazy">
  <div class="text">
    <div class="img-name">${imgName}</div>
    <div class="sm-text">${formatBytes(imgSize)}</div>
  </div>
  `;
};

async function createImages() {
  const fragment = document.createDocumentFragment();
  dbImgGallery = await window.dbConsultas.listar();
  dbImgGallery.forEach(image => {
    const imgCard = document.createElement("div");
    imgCard.classList.add("gallery-item");
    imgCard.innerHTML = imgsCard(image);
    fragment.append(imgCard);
  });
  gallery_container.append(fragment);
};

createImages();

// Evento de escucha para el botón de opciones
$(gallery_container).on("click", ".btn-options", (e) => {
  const menu_options = e.target.closest(".menu-options");
  menu_options.toggleAttribute("data-active-options");
});

// Evento de escucha para activar el popup de cada imagen
$(gallery_container).on("click", "img", (e) => {
  carousel_container.hidden = false;

  const img = e.target;
  const currentItem = img.closest(".gallery-item");
  let index = [...gallery_container.children].indexOf(currentItem);

  setPopupData(img, index);
  img.closest(".gallery-item").setAttribute("data-active", true);
});

// Evento para cerrar el carrusel de Imágenes
carousel_btn_close.addEventListener("click", () => {
  carousel_container.hidden = true;
  gallery_container.querySelector("[data-active]").removeAttribute("data-active");
});

// Funcionalidad para agregar imagen
btn_add.addEventListener("click", () => {
  console.log("Modal de adición");
});

// Funcionalidad para eliminar imagen
$(gallery_container).on("click", ".btn-delete", (e) => {
  const galleryItem = e.target.closest(".gallery-item");
  const deletionImg = galleryItem.querySelector("img")
  console.log(deletionImg.getAttribute("data-id"));
  Swal.fire({
    title: 'Estás Seguro?',
    text: "No podrás revertir esta acción!",
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#d33',
    confirmButtonText: 'Si, Eliminar!',
    cancelButtonText: 'Cancelar'
  }).then((result) => {
    if (result.isConfirmed) {
      galleryItem.remove();
      window.dbConsultas.eliminar(deletionImg.getAttribute("data-id"), deletionImg.getAttribute("src"));

      Swal.fire(
        'Borrada!',
        'Tu imagen ha sido eliminada.',
        'success'
      )
    }
  });
});

// Funcionalidad para editar imagen
$(gallery_container).on("click", ".btn-edit", (e) => {
  modifyGalleryItem = e.target.closest(".gallery-item");
  const editImg = modifyGalleryItem.querySelector("img")
  console.log(editImg.getAttribute("data-id"));
  const dataImgItem = dbImgGallery.find(element => element.idImg === +editImg.getAttribute("data-id"));

  $("#editImgName").val(editImg.getAttribute("alt"));
  $("#editImgDescription").val(dataImgItem.imgDescription);
});

// Formatea el valor del tamaño de mi imagen
function formatBytes(bytes, decimals = 2) {
  if (!+bytes) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

// Asigna los datos del Popup
function setPopupData(image, itemIndex) {
  const dataImgItem = dbImgGallery.find(element => element.idImg === +image.getAttribute("data-id"));
  carousel_img.src = image.getAttribute("src");
  carousel_img.alt = image.getAttribute("alt");
  carousel_img_name.innerText = image.getAttribute("alt");
  carousel_img_size.innerText = formatBytes(dataImgItem.imgSize);  
  carousel_position_cnt.innerText = `Imagen ${itemIndex + 1} de ${gallery_container.children.length}`;
  carousel_info_text.innerText = dataImgItem.imgDescription;
};

const addForm = document.querySelector('#addForm');
addForm.addEventListener('submit', async function (event) {
  event.preventDefault();
  event.stopPropagation();
  if (addForm.checkValidity()) {
    const imgInput = event.target.querySelector("#NewImg");
    const imgFile = imgInput.files[0];
    let newGalleryItem = {
      imgName: $("#NewImgName").val(),
      imgDescription: $("#NewImgDescription").val(),
      imgSize: imgFile.size
    };

    console.log(imgFile);

    if (!isFileImage(imgFile)) {
      Swal.fire({
        icon: 'error',
        title: 'Oops...',
        text: 'El archivo que seleccionaste no es un tipo de imagen válido!',
      });
      $("#NewImg").val("");
      return;
    }
    
    newGalleryItem = await window.dbConsultas.crear(newGalleryItem, imgFile.path);
    const imgCard = document.createElement("div");
    imgCard.classList.add("gallery-item");
    imgCard.innerHTML = imgsCard(newGalleryItem);
    gallery_container.prepend(imgCard);
    dbImgGallery.push(newGalleryItem);


    $("#addModal").modal("toggle");
  };
  addForm.classList.add('was-validated')
}, false)


const editForm = document.querySelector('#editForm');
editForm.addEventListener('submit', function (event) {
  event.preventDefault();
  event.stopPropagation();
  if (editForm.checkValidity()) {
    const editImg = modifyGalleryItem.querySelector("img");
    const editText =  modifyGalleryItem.querySelector(".img-name");
    const dataImgItem = dbImgGallery.find(element => element.idImg === +editImg.getAttribute("data-id"));
    const editGalleryItem = {
      imgName: $("#editImgName").val(),
      imgDescription: $("#editImgDescription").val(),
    };

    editImg.setAttribute("alt", editGalleryItem.imgName);
    editText.innerText = editGalleryItem.imgName;

    dataImgItem.imgName = editGalleryItem.imgName;
    dataImgItem.imgDescription = editGalleryItem.imgDescription;
    window.dbConsultas.editar(editGalleryItem, editImg.getAttribute("data-id"));

    $("#editModal").modal("toggle");
  };
  editForm.classList.add('was-validated')
}, false)


function isFileImage(file) {
  const acceptedImageTypes = ['image/gif', 'image/png', 'image/jpeg', 'image/webp'];
  return file && acceptedImageTypes.includes(file['type']);
};


// Resetear modal
$('.modal').on('hidden.bs.modal', function () {
  $(this).find('form').trigger('reset').removeClass('was-validated');
});