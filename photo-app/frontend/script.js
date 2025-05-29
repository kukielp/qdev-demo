// Configuration
const API_ENDPOINT = 'https://your-api-endpoint.execute-api.region.amazonaws.com'; // Replace with your actual API endpoint

// DOM Elements
const uploadForm = document.getElementById('upload-form');
const photoInput = document.getElementById('photo-input');
const previewImage = document.getElementById('preview-image');
const uploadStatus = document.getElementById('upload-status');
const photoList = document.getElementById('photo-list');
const noPhotosMessage = document.getElementById('no-photos-message');
const photoDetail = document.getElementById('photo-detail');
const photoDetailTitle = document.getElementById('photo-detail-title');
const photoDetailImage = document.getElementById('photo-detail-image');
const photoDetailFilename = document.getElementById('photo-detail-filename');
const photoDetailDate = document.getElementById('photo-detail-date');
const photoDetailDownload = document.getElementById('photo-detail-download');
const photoDetailClose = document.getElementById('photo-detail-close');

// Local storage key for storing photo IDs
const PHOTO_IDS_KEY = 'photoAppPhotoIds';

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Show preview when a file is selected
    photoInput.addEventListener('change', showPreview);
    
    // Handle form submission
    uploadForm.addEventListener('submit', uploadPhoto);
    
    // Close photo detail view
    photoDetailClose.addEventListener('click', () => {
        photoDetail.style.display = 'none';
    });
    
    // Load photos from local storage
    loadPhotos();
});

// Functions
function showPreview(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            previewImage.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
}

async function uploadPhoto(event) {
    event.preventDefault();
    
    const file = photoInput.files[0];
    if (!file) {
        showStatus('Please select a photo to upload', 'error');
        return;
    }
    
    // Show loading status
    showStatus('Uploading photo...', '');
    
    try {
        // Read file as base64
        const base64Photo = await readFileAsBase64(file);
        
        // Prepare request payload
        const payload = {
            photo: base64Photo,
            fileName: file.name
        };
        
        // Send request to API
        const response = await fetch(`${API_ENDPOINT}/photos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Save photo ID to local storage
        savePhotoId(data.photoId);
        
        // Show success message
        showStatus('Photo uploaded successfully!', 'success');
        
        // Reset form
        uploadForm.reset();
        previewImage.style.display = 'none';
        
        // Reload photos
        loadPhotos();
        
    } catch (error) {
        console.error('Error uploading photo:', error);
        showStatus(`Error uploading photo: ${error.message}`, 'error');
    }
}

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = 'status';
    if (type) {
        uploadStatus.classList.add(type);
    }
}

function savePhotoId(photoId) {
    let photoIds = JSON.parse(localStorage.getItem(PHOTO_IDS_KEY)) || [];
    photoIds.push({
        id: photoId,
        timestamp: new Date().toISOString()
    });
    localStorage.setItem(PHOTO_IDS_KEY, JSON.stringify(photoIds));
}

async function loadPhotos() {
    // Get photo IDs from local storage
    const photoIds = JSON.parse(localStorage.getItem(PHOTO_IDS_KEY)) || [];
    
    // Clear photo list
    while (photoList.firstChild && photoList.firstChild !== noPhotosMessage) {
        photoList.removeChild(photoList.firstChild);
    }
    
    // Show/hide no photos message
    if (photoIds.length === 0) {
        noPhotosMessage.style.display = 'block';
        return;
    } else {
        noPhotosMessage.style.display = 'none';
    }
    
    // Sort photos by timestamp (newest first)
    photoIds.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Load each photo
    for (const photoData of photoIds) {
        try {
            await loadPhoto(photoData.id);
        } catch (error) {
            console.error(`Error loading photo ${photoData.id}:`, error);
        }
    }
}

async function loadPhoto(photoId) {
    try {
        // Fetch photo metadata from API
        const response = await fetch(`${API_ENDPOINT}/photos/${photoId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const photoData = await response.json();
        
        // Create photo item element
        const photoItem = document.createElement('div');
        photoItem.className = 'photo-item';
        photoItem.dataset.photoId = photoId;
        
        // Create image element
        const img = document.createElement('img');
        img.src = photoData.downloadUrl;
        img.alt = photoData.fileName;
        
        // Add click event to show photo detail
        photoItem.addEventListener('click', () => showPhotoDetail(photoData));
        
        // Add image to photo item
        photoItem.appendChild(img);
        
        // Add photo item to photo list
        photoList.appendChild(photoItem);
        
    } catch (error) {
        console.error(`Error loading photo ${photoId}:`, error);
    }
}

function showPhotoDetail(photoData) {
    // Set photo detail content
    photoDetailTitle.textContent = photoData.fileName;
    photoDetailImage.src = photoData.downloadUrl;
    photoDetailFilename.textContent = photoData.fileName;
    photoDetailDate.textContent = new Date(photoData.uploadTimestamp).toLocaleString();
    photoDetailDownload.href = photoData.downloadUrl;
    photoDetailDownload.download = photoData.fileName;
    
    // Show photo detail
    photoDetail.style.display = 'block';
}

// Helper function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}