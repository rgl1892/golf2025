document.addEventListener('DOMContentLoaded', function() {
    // Only run on carousel image admin pages
    if (!document.querySelector('#id_focal_point_x')) return;
    
    const focalXInput = document.querySelector('#id_focal_point_x');
    const focalYInput = document.querySelector('#id_focal_point_y');
    const imageField = document.querySelector('#id_image');
    
    // Create enhanced focal point interface
    createFocalPointInterface();
    
    function createFocalPointInterface() {
        const focalSection = document.querySelector('.field-focal_point_x').parentNode;
        
        // Create container
        const container = document.createElement('div');
        container.className = 'focal-grid';
        
        // Controls section
        const controlsDiv = document.createElement('div');
        controlsDiv.innerHTML = `
            <div class="focal-point-controls">
                <div class="focal-point-field">
                    <label>X Position (Left ← → Right)</label>
                    <input type="range" id="focal_x_range" min="0" max="100" value="${focalXInput.value}">
                    <span id="focal_x_value">${focalXInput.value}%</span>
                </div>
                <div class="focal-point-field">
                    <label>Y Position (Top ↑ ↓ Bottom)</label>
                    <input type="range" id="focal_y_range" min="0" max="100" value="${focalYInput.value}">
                    <span id="focal_y_value">${focalYInput.value}%</span>
                </div>
            </div>
            <div class="focal-instructions">
                💡 <strong>Tip:</strong> Drag the sliders to adjust where the image is centered in the carousel. 
                The red dot shows the focal point on the preview.
            </div>
        `;
        
        // Preview section
        const previewDiv = document.createElement('div');
        previewDiv.className = 'focal-point-preview';
        previewDiv.innerHTML = `
            <h4>🖼️ Preview (Carousel Size)</h4>
            <div class="preview-container">
                <img id="preview_image" class="preview-image" src="" alt="Preview">
                <div id="focal_indicator" class="focal-point-indicator"></div>
            </div>
        `;
        
        container.appendChild(controlsDiv);
        container.appendChild(previewDiv);
        
        // Insert after the focal point fields
        focalSection.appendChild(container);
        
        // Setup event listeners
        setupEventListeners();
        
        // Initial preview update
        updatePreview();
    }
    
    function setupEventListeners() {
        const xRange = document.querySelector('#focal_x_range');
        const yRange = document.querySelector('#focal_y_range');
        const xValue = document.querySelector('#focal_x_value');
        const yValue = document.querySelector('#focal_y_value');
        
        // X slider
        xRange.addEventListener('input', function() {
            focalXInput.value = this.value;
            xValue.textContent = this.value + '%';
            updatePreview();
        });
        
        // Y slider  
        yRange.addEventListener('input', function() {
            focalYInput.value = this.value;
            yValue.textContent = this.value + '%';
            updatePreview();
        });
        
        // Sync with number inputs
        focalXInput.addEventListener('input', function() {
            xRange.value = this.value;
            xValue.textContent = this.value + '%';
            updatePreview();
        });
        
        focalYInput.addEventListener('input', function() {
            yRange.value = this.value;
            yValue.textContent = this.value + '%';
            updatePreview();
        });
        
        // Image upload change
        imageField.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const previewImage = document.querySelector('#preview_image');
                    if (previewImage) {
                        previewImage.src = e.target.result;
                        previewImage.style.display = 'block';
                        document.querySelector('#focal_indicator').style.display = 'block';
                        updatePreview();
                    }
                };
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }
    
    function updatePreview() {
        const previewImage = document.querySelector('#preview_image');
        const focalIndicator = document.querySelector('#focal_indicator');
        
        if (!previewImage || !focalIndicator) {
            console.log('Preview elements not found');
            return;
        }
        
        const x = focalXInput.value || 50;
        const y = focalYInput.value || 50;
        
        console.log(`Updating focal point to: ${x}%, ${y}%`);
        
        // Update image positioning
        previewImage.style.objectPosition = `${x}% ${y}%`;
        
        // Update focal point indicator position
        focalIndicator.style.left = `${x}%`;
        focalIndicator.style.top = `${y}%`;
        focalIndicator.style.display = 'block';
        
        // Try to load current image if not already loaded
        if (!previewImage.src || previewImage.src.includes('data:') === false) {
            const currentImageSrc = getCurrentImageSrc();
            if (currentImageSrc) {
                console.log('Loading image:', currentImageSrc);
                previewImage.src = currentImageSrc;
                previewImage.style.display = 'block';
                
                // Ensure indicator shows after image loads
                previewImage.onload = function() {
                    focalIndicator.style.display = 'block';
                };
            } else {
                console.log('No image source available');
                // Show placeholder
                previewImage.style.display = 'none';
                focalIndicator.style.display = 'block'; // Still show dot for positioning reference
            }
        }
    }
    
    function getCurrentImageSrc() {
        // First, try to get existing image from "Currently" link
        const currentlyLink = document.querySelector('.field-image p.file a');
        if (currentlyLink) {
            return currentlyLink.href;
        }
        
        // Try alternative selector for current image
        const imageLink = document.querySelector('a[href*="/media/carousel/"]');
        if (imageLink) {
            return imageLink.href;
        }
        
        // For new uploads, create object URL from file input
        const fileInput = document.querySelector('#id_image');
        if (fileInput && fileInput.files && fileInput.files[0]) {
            return URL.createObjectURL(fileInput.files[0]);
        }
        
        console.log('No image source found'); // Debug log
        return null;
    }
});