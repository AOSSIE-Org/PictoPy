document.addEventListener('DOMContentLoaded', () => {
    document.body.addEventListener('click', (event) => {
        const target = event.target;

        if (target.classList.contains('section')) {
            if (!target.classList.contains('clicked')) {
                document.querySelectorAll('img.section.clicked').forEach(clickedImg => {
                    clickedImg.classList.remove('clicked');
                });

                target.classList.add('clicked');
            }
        }

        if (target.classList.contains('toggle')) {
            target.classList.toggle('enabled');
        }

        if (target.classList.contains('button')) {
            target.classList.toggle('clicked');
        }
    });
});
