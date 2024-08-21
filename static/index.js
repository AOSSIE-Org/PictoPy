// Initialize variables
let currentMediaIndex = -1;
let currentMediaArray = [];
let currentMediaTypesArray = [];
let selectedMedia = [];
let selectionMode = false;
let section = "img";
let groupBy = "directory";
let openedGroup = "";
let fetchController;
let isShowingInfo = false;

// Navbar configuration
const navConfig = {
    default: [
        { src: "/static/icons/ai.svg", alt: "AI Tags", class: "toggle", onclick: "toggleGroup(this)" },
        { src: "/static/icons/images.svg", alt: "Images", class: "section", onclick: "displayData('img', this)" },
        { src: "/static/icons/videos.svg", alt: "Videos", class: "section", onclick: "displayData('vid', this)" },
        { src: "/static/icons/hide.svg", alt: "Hidden Files", class: "section", onclick: "displayData('hidden', this)" },
        { src: "/static/icons/delete.svg", alt: "Trash", class: "section", onclick: "displayData('trash', this)" },
        { src: "/static/icons/select.svg", alt: "Enable Selection Mode", class: "toggle", onclick: "toggleSelectionMode()" }
    ],
    selection: {
        img: [
            { src: "/static/icons/hide.svg", alt: "Hide", class: "button", onclick: "sendSelectedMedia('/hide')" },
            { src: "/static/icons/delete.svg", alt: "Delete", class: "button", onclick: "sendSelectedMedia('/toTrash')" }
        ],
        vid: [
            { src: "/static/icons/hide.svg", alt: "Hide", class: "button", onclick: "sendSelectedMedia('/hide')" },
            { src: "/static/icons/delete.svg", alt: "Delete", class: "button", onclick: "sendSelectedMedia('/toTrash')" }
        ],
        hidden: [
            { src: "/static/icons/unhide.svg", alt: "Unhide", class: "button", onclick: "sendSelectedMedia('/unhide')" },
            { src: "/static/icons/delete.svg", alt: "Delete", class: "button", onclick: "sendSelectedMedia('/toTrash')" }
        ],
        trash: [
            { src: "/static/icons/restore.svg", alt: "Restore", class: "button", onclick: "sendSelectedMedia('/restore')" },
            { src: "/static/icons/delete.svg", alt: "Delete", class: "button", onclick: "sendSelectedMedia('/delete')" }
        ],
        toggleSelect: [
            { src: "/static/icons/select.svg", alt: "Disable Selection Mode", class: "select", onclick: "toggleSelectionMode()" }
        ]
    },
    media: [
        { src: "/static/icons/info.svg", alt: "Info", class: "toggle", onclick: "toggleInfo()" },
        { src: "/static/icons/previous.svg", alt: "Previous", class: "button", onclick: "prevMedia()" },
        { src: "/static/icons/next.svg", alt: "Next", class: "button", onclick: "nextMedia()" },
        { src: "/static/icons/close.svg", alt: "Close", class: "button", onclick: "closeMedia()" }
    ]
};

// Initial navbar
requestAnimationFrame(updateNavbar);

// Display default section
displayData(section, null);

// Fetch data from a route
async function readRoute(route, button) {
    if (fetchController !== undefined) { 
        fetchController.abort(); 
    }
    fetchController = new AbortController(); 
    const { originalSrc, originalCursor } = showLoading(button);
    try {
        // const { signal } = fetchController; 
        // const response = await fetch(route, { signal });
        const response = await fetch(route, { signal: fetchController.signal });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        hideLoading(button, originalSrc, originalCursor);
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch data from ${route}:`, error);
        return null;
    }
}

function showLoading(button) {
    if (!button) return { originalSrc: '', originalCursor: '' };

    const originalSrc = button.getAttribute('src');
    const originalCursor = button.style.cursor;
    button.setAttribute('src', '/static/icons/loading.svg');
    button.style.cursor = 'wait';
    return { originalSrc, originalCursor };
}

function hideLoading(button, originalSrc, originalCursor) {
    if (!button) return;

    button.setAttribute('src', originalSrc);
    button.style.cursor = originalCursor;
}

// Get thumbnail URL based on the media type
async function getThumbnail(path, type) {
    if (type === 'vid') {
        return `/thumbnail/${path}`;
    } else {
        return `/media/${path}`;
    }
}

// Fetch thumbnails for a list of paths and types
async function fetchThumbnails(paths, types) {
    const thumbnailsPromises = paths.map(async (path, index) => {
        const fileType = types[index];
        return getThumbnail(path, fileType);
    });

    return await Promise.all(thumbnailsPromises);
}

// Create a card element
function createCard(type, thumbnailSrc, altText, name = '', pathsArray = [], typesArray = [], index = -1) {
    const card = document.createElement('div');
    card.className = 'card';
    card.dataset.type = type;

    if (type === 'group') {
        card.classList.add('group');
        card.innerHTML = `
            <img src="${thumbnailSrc}" alt="${altText}" class="thumbnail">
            <div class="group-name">${name}</div>
        `;
        card.addEventListener('click', () => handleGroupClick(name, pathsArray, typesArray, index));
    } else {
        card.innerHTML = `
            <img src="${thumbnailSrc}" alt="${altText}" class="thumbnail">
        `;
        card.addEventListener('click', () => handleMediaClick(pathsArray, typesArray, index));
    }

    return card;
}

// Handle group card click
function handleGroupClick(name, pathsArray, typesArray, index) {
    if (selectionMode) {
        toggleGroupSelection(pathsArray);
    } else {
        displayGroup(name, pathsArray, typesArray, index);
    }
}

// Handle media card click
function handleMediaClick(pathsArray, typesArray, index) {
    if (selectionMode) {
        toggleMediaSelection(pathsArray[index]);
    } else {
        openMedia(pathsArray, index, typesArray);
    }
}

// Display group cards with data
async function displayData(_section, button) {
    section = _section;
    const data = await readRoute(`/${section}/${groupBy}`, button);
    const container = document.getElementById('dataContainer');

    if (!data || !container) {
        if (container) container.textContent = 'Failed to fetch data.';
        return;
    }

    container.innerHTML = '';

    for (const [groupName, paths, types] of data) {
        const pathsArray = paths.split(',').map(s => s.trim());
        const typesArray = types.split(',').map(s => s.trim());

        const thumbnails = await fetchThumbnails(pathsArray, typesArray);

        const groupCard = createCard('group', thumbnails[0], groupName, groupName, pathsArray, typesArray);
        container.appendChild(groupCard);

        if (openedGroup === groupName && selectionMode) {
            displayGroup(groupName, pathsArray, typesArray);
            break;
        }
    }
}

// Display media cards within a group
async function displayGroup(groupName, pathsArray, typesArray) {
    openedGroup = groupName;
    const container = document.getElementById('dataContainer');
    
    if (!container) {
        console.error('Container element not found');
        return;
    }

    container.innerHTML = '';

    for (let i = 0; i < pathsArray.length; i++) {
        const path = pathsArray[i].trim();
        const fileType = typesArray[i];
        const thumbnail = await getThumbnail(path, fileType);

        const mediaCard = createCard('media', thumbnail, groupName, '', pathsArray, typesArray, i);
        container.appendChild(mediaCard);
    }
}

// Open a media file in a floating window
function openMedia(mediaArray, mediaIndex, typesArray) {
    updateNavbar('media');
    currentMediaArray = mediaArray;
    currentMediaIndex = mediaIndex;
    currentMediaTypesArray = typesArray; 

    const mediaUrl = `/media/${currentMediaArray[currentMediaIndex]}`;
    const mediaType = currentMediaTypesArray[currentMediaIndex]; 
    const mediaContent = document.getElementById('mediaContent');
    const floatingWindow = document.getElementById('floatingWindow');
    if (isShowingInfo) {
        showInfo(mediaContent)
    } else {
        // Media View
        if (mediaType === 'vid') {
            mediaContent.innerHTML = `<video src="${mediaUrl}" controls autoplay style="max-width: 100%; max-height: 100%;"></video>`;
        } else {
            mediaContent.innerHTML = `<img src="${mediaUrl}" alt="Media" style="max-width: 100%; max-height: 100%;">`;
        }
    }

    floatingWindow.style.display = 'block';
}

// Close the floating media window
function closeMedia() {
    isShowingInfo = false;
    const floatingWindow = document.getElementById('floatingWindow');
    floatingWindow.style.display = 'none';
    document.getElementById('mediaContent').innerHTML = '';

    // Update navbar immediately after closing the media window
    updateNavbar();
}

// Navigate to the previous media item
function prevMedia() {
    // isShowingInfo = false;
    if (currentMediaIndex > 0) {
        openMedia(currentMediaArray, currentMediaIndex - 1, currentMediaTypesArray);
    }
}

// Navigate to the next media item
function nextMedia() {
    // isShowingInfo = false;
    if (currentMediaIndex < currentMediaArray.length - 1) {
        openMedia(currentMediaArray, currentMediaIndex + 1, currentMediaTypesArray);
    }
}

// Toggle grouping of media
function toggleGroup(button) {
    groupBy = (groupBy === 'class') ? 'directory' : 'class';
    displayData(section, button);
}

// Toggle selection mode
function toggleSelectionMode() {
    selectionMode = !selectionMode;
    for (const card of document.getElementsByClassName('card')) {
        card.classList.toggle('selected', selectedMedia.includes(card.querySelector('img').src));
    }
    selectedMedia = [];
    // Deferred navbar update
    requestAnimationFrame(updateNavbar);
}

// Toggle selection of a media item
function toggleMediaSelection(path) {
    const index = selectedMedia.indexOf(path);
    if (index === -1) {
        selectedMedia.push(path);
    } else {
        selectedMedia.splice(index, 1);
    }
    updateCardSelection(path);
}

// Toggle selection of all media items in a group
function toggleGroupSelection(pathsArray) {
    for (const path of pathsArray) {
        toggleMediaSelection(path.trim());
    }
}

// Update the selection status of a card
function updateCardSelection(path) {
    console.log(`Called updateCardSelection with path: ${path}`);
    const cards = document.getElementsByClassName('card');
    console.log(`Found ${cards.length} cards`);
    for (const card of cards) {
        console.log(`Processing card: ${card.outerHTML}`);
        if (card.querySelector('img').src.endsWith(path.replace(/\\/g, '/'))) {
            card.classList.toggle('selected', selectedMedia.includes(path));
            console.log("Selected");
        }
    }
}

// Send selected media paths to the specified route
async function sendSelectedMedia(route) {
    if (selectedMedia.length === 0) return;

    try {
        const response = await fetch(route, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ selectedMedia: selectedMedia })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        selectedMedia = [];
        displayData(section);
    } catch (error) {
        console.error(`Failed to send selected media to ${route}:`, error);
    }
}

// Update the navigation bar based on the current state
function updateNavbar(mode = 'default') {
    const floatingNavCard = document.getElementById('floatingNavCard');
    floatingNavCard.innerHTML = '';

    let navItems = [];

    if (mode === 'media') {
        navItems = navConfig.media;
    } else if (selectionMode && navConfig.selection[section]) {
        navItems = [...navConfig.selection[section], ...navConfig.selection.toggleSelect];
    } else {
        navItems = navConfig.default;
    }

    // Use DocumentFragment to minimize DOM manipulations
    const fragment = document.createDocumentFragment();
    navItems.forEach(item => {
        const navIcon = document.createElement('img');
        navIcon.src = item.src;
        navIcon.alt = item.alt;
        navIcon.title = item.alt;
        navIcon.className = item.class;
        navIcon.onclick = new Function(item.onclick);

        const navItem = document.createElement('div');
        navItem.className = 'nav-icon';
        navItem.appendChild(navIcon);

        fragment.appendChild(navItem);
    });

    floatingNavCard.appendChild(fragment);
}

// Fetch Media information
async function fetchMediaInfo() {
    if (currentMediaIndex === -1) return {}; // Return empty object if no media is selected

    const mediaPath = `/info/${currentMediaArray[currentMediaIndex]}`;
    const mediaInfo = await readRoute(mediaPath);

    return mediaInfo;
}

// Toggle between media and info
function toggleInfo() {
    isShowingInfo = !isShowingInfo;
    openMedia(currentMediaArray, currentMediaIndex, currentMediaTypesArray);
}

// Info View
function showInfo(mediaContent) {
    fetchMediaInfo().then(info => {
        let infoHtml = `
            <table class="info-table">
                <tbody>
        `;

        for (const [key, value] of Object.entries(info)) {
            if (Array.isArray(value)) {
                infoHtml += `
                    <tr>
                        <th>${key}</th>
                        <td>${value.map(tag => `<span class="tag-button">${tag}</span>`).join('')}</td>
                    </tr>
                `;
            } else {
                infoHtml += `
                    <tr>
                        <th>${key}</th>
                        <td>${value}</td>
                    </tr>
                `;
            }
        }

        infoHtml += `
                </tbody>
            </table>
        `;

        mediaContent.innerHTML = infoHtml;
    });
}
