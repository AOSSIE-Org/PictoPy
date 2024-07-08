// Function to send selected data to Flask route
function callRoute(route) {
    var selectedImages = [];

    // Collect selected image paths
    var imageCheckboxes = document.querySelectorAll('input[name="selectedImages[]"]:checked');
    imageCheckboxes.forEach(function(checkbox) {
        selectedImages.push(checkbox.value);
    });

    // Send selected data to Flask route
    fetch(`/${route}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            selectedImages: selectedImages
        })
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;  // Redirect to the new URL
        } else {
            console.log(response);  // Log the response if not redirected (for debugging)
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Function to handle class checkbox check/uncheck
function toggleClass(className) {
    var classCheckbox = document.getElementById(className);
    var mediaImagesCheckboxes = document.querySelectorAll('.mediaImages .' + className);
    mediaImagesCheckboxes.forEach(function(checkbox) {
        checkbox.checked = classCheckbox.checked;
    });
    console.log(document.querySelectorAll('input[name="selectedImages[]"]:checked'));
}
