// Initialize Vue application
const { createApp } = Vue;

createApp({
    data() {
        return {
            // Data could be added here if we need dynamic content later
        }
    },
    mounted() {
        // Add cool animation effects
        this.addAnimationEffects();
    },
    methods: {
        addAnimationEffects() {
            // Subtle pulsating effect for diagram elements
            const iconBoxes = document.querySelectorAll('.icon-box');
            
            iconBoxes.forEach((box, index) => {
                // Add a slight delay between animations
                setTimeout(() => {
                    this.addPulseEffect(box);
                }, index * 200);
            });
            
            // Add hover effects for better interaction
            this.addHoverEffects();
            
            // Add some subtle background effects
            this.addBackgroundEffect();
        },
        
        addPulseEffect(element) {
            // Create keyframes for subtle pulsating
            element.animate([
                { transform: 'scale(1)', opacity: 1 },
                { transform: 'scale(1.05)', opacity: 1 },
                { transform: 'scale(1)', opacity: 1 }
            ], {
                duration: 2000,
                iterations: Infinity
            });
        },
        
        addHoverEffects() {
            // Add hover effect to flow items
            const flowItems = document.querySelectorAll('.flow-item');
            
            flowItems.forEach(item => {
                item.addEventListener('mouseenter', () => {
                    const iconBox = item.querySelector('.icon-box');
                    if (iconBox) {
                        iconBox.style.transform = 'scale(1.1)';
                        iconBox.style.boxShadow = '0 0 15px rgba(255, 255, 255, 0.5)';
                        iconBox.style.transition = 'all 0.3s ease';
                    }
                });
                
                item.addEventListener('mouseleave', () => {
                    const iconBox = item.querySelector('.icon-box');
                    if (iconBox) {
                        iconBox.style.transform = 'scale(1)';
                        iconBox.style.boxShadow = 'none';
                    }
                });
            });
        },
        
        addBackgroundEffect() {
            // Add subtle gradient animation to background
            const container = document.querySelector('.knowledge-base-container');
            if (container) {
                container.style.backgroundImage = 'linear-gradient(45deg, #0c0c18 0%, #221a35 50%, #1a1a3a 100%)';
                container.style.backgroundSize = '200% 200%';
                container.style.animation = 'gradientBackground 15s ease infinite';
                
                // Add keyframes for background animation
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes gradientBackground {
                        0% { background-position: 0% 50%; }
                        50% { background-position: 100% 50%; }
                        100% { background-position: 0% 50%; }
                    }
                `;
                document.head.appendChild(style);
            }
        },
        
        // Method to simulate drawing connections between elements
        // Can be extended with SVG paths for more complex connections
        drawConnections() {
            // This would require a canvas or SVG implementation
            // For a more advanced version, we could use libraries like d3.js
            console.log("Connection drawing would be implemented here");
        }
    }
}).mount('#app');