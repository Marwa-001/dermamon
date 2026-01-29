// Draggable Widget Functionality
class DraggableWidget {
    constructor(elementId) {
        this.element = document.getElementById(elementId);
        this.isDragging = false;
        this.currentX = 0;
        this.currentY = 0;
        this.initialX = 0;
        this.initialY = 0;
        this.xOffset = 0;
        this.yOffset = 0;
        
        if (this.element) {
            this.init();
            this.loadPosition(elementId);
        }
    }
    
    init() {
        // Mouse events
        this.element.addEventListener('mousedown', this.dragStart.bind(this));
        document.addEventListener('mousemove', this.drag.bind(this));
        document.addEventListener('mouseup', this.dragEnd.bind(this));
        
        // Touch events
        this.element.addEventListener('touchstart', this.dragStart.bind(this));
        document.addEventListener('touchmove', this.drag.bind(this));
        document.addEventListener('touchend', this.dragEnd.bind(this));
        
        // Prevent default drag behavior
        this.element.addEventListener('dragstart', (e) => e.preventDefault());
    }
    
    dragStart(e) {
        // Don't drag if clicking on the widget content to open
        if (e.target.closest('.widget-content') && !e.ctrlKey && !e.metaKey) {
            return;
        }
        
        if (e.type === 'touchstart') {
            this.initialX = e.touches[0].clientX - this.xOffset;
            this.initialY = e.touches[0].clientY - this.yOffset;
        } else {
            this.initialX = e.clientX - this.xOffset;
            this.initialY = e.clientY - this.yOffset;
        }
        
        // Check if we're starting the drag (ctrl/cmd key or long press)
        if (e.ctrlKey || e.metaKey || e.type === 'touchstart') {
            this.isDragging = true;
            this.element.classList.add('dragging');
        }
    }
    
    drag(e) {
        if (!this.isDragging) return;
        
        e.preventDefault();
        
        if (e.type === 'touchmove') {
            this.currentX = e.touches[0].clientX - this.initialX;
            this.currentY = e.touches[0].clientY - this.initialY;
        } else {
            this.currentX = e.clientX - this.initialX;
            this.currentY = e.clientY - this.initialY;
        }
        
        this.xOffset = this.currentX;
        this.yOffset = this.currentY;
        
        this.setTranslate(this.currentX, this.currentY);
    }
    
    dragEnd(e) {
        if (!this.isDragging) return;
        
        this.initialX = this.currentX;
        this.initialY = this.currentY;
        
        this.isDragging = false;
        this.element.classList.remove('dragging');
        
        // Save position
        this.savePosition();
    }
    
    setTranslate(xPos, yPos) {
        // Get element's current position
        const rect = this.element.getBoundingClientRect();
        const elementWidth = rect.width;
        const elementHeight = rect.height;
        
        // Get viewport dimensions
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Calculate boundaries
        const maxX = viewportWidth - elementWidth - 20;
        const maxY = viewportHeight - elementHeight - 20;
        const minX = 20;
        const minY = 20;
        
        // Constrain position to viewport
        const constrainedX = Math.max(minX - rect.left, Math.min(xPos, maxX - rect.left + this.xOffset));
        const constrainedY = Math.max(minY - rect.top, Math.min(yPos, maxY - rect.top + this.yOffset));
        
        this.element.style.transform = `translate(${constrainedX}px, ${constrainedY}px)`;
    }
    
    savePosition() {
        const id = this.element.id;
        localStorage.setItem(`${id}_x`, this.xOffset);
        localStorage.setItem(`${id}_y`, this.yOffset);
    }
    
    loadPosition(id) {
        const savedX = localStorage.getItem(`${id}_x`);
        const savedY = localStorage.getItem(`${id}_y`);
        
        if (savedX !== null && savedY !== null) {
            this.xOffset = parseFloat(savedX);
            this.yOffset = parseFloat(savedY);
            this.setTranslate(this.xOffset, this.yOffset);
        }
    }
}

// Initialize draggable widgets when page loads
window.addEventListener('load', () => {
    // Small delay to ensure elements are loaded
    setTimeout(() => {
        new DraggableWidget('gameWidget');
        new DraggableWidget('chatWidget');
    }, 500);
});

// Add instructions on first load
window.addEventListener('load', () => {
    const hasSeenInstructions = localStorage.getItem('hasSeenDragInstructions');
    
    if (!hasSeenInstructions) {
        setTimeout(() => {
            showSuccess('💡 Tip: Hold Ctrl (or Cmd on Mac) and drag the chat/game buttons to move them!');
            localStorage.setItem('hasSeenDragInstructions', 'true');
        }, 3000);
    }
});