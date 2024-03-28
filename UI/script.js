// script.js
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('.horizontal-scroll img');
    const container = document.querySelector('.container');

    images.forEach(image => {
        image.addEventListener('click', function() {
            const overlay = document.createElement('div');
            overlay.classList.add('overlay');
            container.appendChild(overlay);

            const enlargedImage = document.createElement('img');
            enlargedImage.src = this.src;
            enlargedImage.alt = this.alt;
            enlargedImage.classList.add('enlarged-image');
            overlay.appendChild(enlargedImage);

            overlay.addEventListener('click', function() {
                overlay.remove();
            });
        });
    });
});
