/**
 * Magic Carpet Effect for ReconScraper
 * 
 * This script adds floating card effects with purple vapor particles
 * to create a magical carpet visualization for tab panels.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Select all cards that should have the magic carpet effect
    const carpetElements = document.querySelectorAll('.card:not(.file-card)');
    
    carpetElements.forEach(function(card) {
        // Add the magic-carpet class
        card.classList.add('magic-carpet');
        
        // Create vapor elements
        for (let i = 0; i < 5; i++) {
            const vapor = document.createElement('div');
            vapor.className = 'vapor';
            // Randomize horizontal position slightly
            vapor.style.left = (10 + (i * 20) + (Math.random() * 10 - 5)) + '%';
            // Randomize animation duration
            vapor.style.animationDuration = (2 + Math.random()) + 's';
            card.appendChild(vapor);
        }
        
        // Add a container div to better handle spacing
        if (!card.parentNode.classList.contains('magic-carpet-container')) {
            const container = document.createElement('div');
            container.className = 'magic-carpet-container';
            card.parentNode.insertBefore(container, card);
            container.appendChild(card);
        }
    });
    
    // Add additional floating effect on hover
    carpetElements.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            // Slow down the floating animation slightly on hover
            this.style.animationDuration = '8s';
            
            // Generate a few more vapor particles on hover
            for (let i = 0; i < 3; i++) {
                const vapor = document.createElement('div');
                vapor.className = 'vapor';
                vapor.style.left = (20 + (Math.random() * 60)) + '%';
                vapor.style.animationDuration = (1.5 + Math.random()) + 's';
                this.appendChild(vapor);
                
                // Remove these additional vapor particles after animation
                setTimeout(() => {
                    if (vapor && vapor.parentNode) {
                        vapor.parentNode.removeChild(vapor);
                    }
                }, 3000);
            }
        });
        
        card.addEventListener('mouseleave', function() {
            // Return to normal animation speed        this.style.animationDuration = '6s';
        });
    });
    
    // Apply a simpler floating effect to file cards
    const fileCards = document.querySelectorAll('.file-card');
    fileCards.forEach(function(card) {
        // Add a modified magic carpet class
        card.classList.add('magic-carpet');
        card.style.animationDuration = '4s';
        card.style.animationDelay = Math.random() * 2 + 's';
        
        // Add just two vapor particles
        for (let i = 0; i < 2; i++) {
            const vapor = document.createElement('div');
            vapor.className = 'vapor';
            vapor.style.left = (30 + (i * 40)) + '%';
            vapor.style.animationDuration = (2 + Math.random()) + 's';
            card.appendChild(vapor);
        }
    });
});
