// ZaloPay Merchant Portal JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeCarousel();
    initializeTabs();
    initializeAccordion();
    initializeSmoothScrolling();
    initializeAnimations();
    initializeFormValidation();
});

// Carousel functionality
function initializeCarousel() {
    const carousel = document.getElementById('solutionCarousel');
    if (carousel) {
        // Auto-play carousel
        const carouselInstance = new bootstrap.Carousel(carousel, {
            interval: 4000,
            wrap: true,
            pause: 'hover'
        });

        // Add smooth transitions
        carousel.addEventListener('slide.bs.carousel', function(e) {
            const activeItem = carousel.querySelector('.carousel-item.active');
            const nextItem = e.relatedTarget;
            
            if (activeItem) {
                activeItem.style.transform = 'scale(1)';
            }
            if (nextItem) {
                nextItem.style.transform = 'scale(1.02)';
            }
        });
    }
}

// Tab functionality
function initializeTabs() {
    // Solution tabs
    const solutionTabs = document.querySelectorAll('#solutionTabs button[data-bs-toggle="pill"]');
    solutionTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            const tabPane = document.querySelector(target);
            
            if (tabPane) {
                // Add animation to tab content
                tabPane.style.opacity = '0';
                tabPane.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    tabPane.style.transition = 'all 0.3s ease';
                    tabPane.style.opacity = '1';
                    tabPane.style.transform = 'translateY(0)';
                }, 50);
            }
        });
    });

    // Business type tabs
    const businessTabs = document.querySelectorAll('#businessTabs button[data-bs-toggle="pill"]');
    businessTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            const tabPane = document.querySelector(target);
            
            if (tabPane) {
                // Animate process steps
                const steps = tabPane.querySelectorAll('.step');
                steps.forEach((step, index) => {
                    step.style.opacity = '0';
                    step.style.transform = 'translateX(-20px)';
                    
                    setTimeout(() => {
                        step.style.transition = 'all 0.3s ease';
                        step.style.opacity = '1';
                        step.style.transform = 'translateX(0)';
                    }, index * 100);
                });
            }
        });
    });
}

// Accordion functionality
function initializeAccordion() {
    const accordionButtons = document.querySelectorAll('.accordion-button');
    
    accordionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-bs-target');
            const accordionBody = document.querySelector(target + ' .accordion-body');
            
            if (accordionBody) {
                // Add smooth animation to accordion content
                setTimeout(() => {
                    accordionBody.style.opacity = '0';
                    accordionBody.style.transform = 'translateY(-10px)';
                    
                    setTimeout(() => {
                        accordionBody.style.transition = 'all 0.2s ease';
                        accordionBody.style.opacity = '1';
                        accordionBody.style.transform = 'translateY(0)';
                    }, 50);
                }, 50);
            }
        });
    });
}

// Smooth scrolling for navigation links
function initializeSmoothScrolling() {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const target = this.getAttribute('href');
            
            // Skip if href is just '#' or empty
            if (!target || target === '#' || target.length <= 1) {
                return;
            }
            
            const targetElement = document.querySelector(target);
            
            if (targetElement) {
                e.preventDefault();
                
                const headerOffset = 80; // Account for fixed header
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
                
                // Update active nav link
                updateActiveNavLink(target);
            }
        });
    });
}

// Update active navigation link
function updateActiveNavLink(target) {
    // Skip if target is invalid
    if (!target || target === '#' || target.length <= 1) {
        return;
    }
    
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === target) {
            link.classList.add('active');
        }
    });
}

// Scroll animations
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                
                // Special animations for specific elements
                if (entry.target.classList.contains('benefit-card')) {
                    animateCards(entry.target.parentElement.querySelectorAll('.benefit-card'));
                } else if (entry.target.classList.contains('solution-card')) {
                    animateCards(entry.target.parentElement.querySelectorAll('.solution-card'));
                } else if (entry.target.classList.contains('business-type-card')) {
                    animateCards(entry.target.parentElement.querySelectorAll('.business-type-card'));
                } else if (entry.target.classList.contains('partner-logo')) {
                    animatePartnerLogos();
                }
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animatedElements = document.querySelectorAll(`
        .section-title,
        .section-subtitle,
        .section-description,
        .benefit-card,
        .solution-card,
        .business-type-card,
        .partner-logo,
        .process-steps,
        .accordion
    `);
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

// Animate cards with stagger effect
function animateCards(cards) {
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Animate partner logos
function animatePartnerLogos() {
    const logos = document.querySelectorAll('.partner-logo');
    logos.forEach((logo, index) => {
        logo.style.opacity = '0';
        logo.style.transform = 'scale(0.8)';
        
        setTimeout(() => {
            logo.style.transition = 'all 0.4s ease';
            logo.style.opacity = '1';
            logo.style.transform = 'scale(1)';
        }, index * 80);
    });
}

// Form validation (for future use)
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
}

// Utility functions
function showLoading(element) {
    if (element) {
        element.classList.add('loading');
        const spinner = document.createElement('span');
        spinner.className = 'spinner ms-2';
        element.appendChild(spinner);
    }
}

function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
        const spinner = element.querySelector('.spinner');
        if (spinner) {
            spinner.remove();
        }
    }
}

// Navigation bar background change on scroll
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.98)';
        navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
        navbar.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
    }
});

// Add click tracking for analytics (placeholder)
function trackEvent(eventName, properties = {}) {
    // This would integrate with analytics service
    console.log('Event tracked:', eventName, properties);
}

// Track CTA button clicks
document.addEventListener('click', function(e) {
    if (e.target.matches('.btn-primary, .hero-cta')) {
        const buttonText = e.target.textContent.trim();
        const section = e.target.closest('section')?.className || 'unknown';
        
        trackEvent('cta_click', {
            button_text: buttonText,
            section: section
        });
    }
});

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle utility
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Performance optimization for scroll events
const throttledScrollHandler = throttle(function() {
    // Handle scroll events here if needed
}, 100);

window.addEventListener('scroll', throttledScrollHandler);

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    // Could send to error tracking service
});

// Add safe querySelector wrapper
function safeQuerySelector(selector) {
    try {
        if (!selector || selector === '#' || selector.trim() === '') {
            return null;
        }
        return document.querySelector(selector);
    } catch (error) {
        console.warn('Invalid selector:', selector, error);
        return null;
    }
}

// Add safe querySelectorAll wrapper
function safeQuerySelectorAll(selector) {
    try {
        if (!selector || selector === '#' || selector.trim() === '') {
            return [];
        }
        return document.querySelectorAll(selector);
    } catch (error) {
        console.warn('Invalid selector:', selector, error);
        return [];
    }
}

// Touch device detection and optimization
function isTouchDevice() {
    return (('ontouchstart' in window) ||
            (navigator.maxTouchPoints > 0) ||
            (navigator.msMaxTouchPoints > 0));
}

if (isTouchDevice()) {
    document.body.classList.add('touch-device');
    
    // Optimize hover effects for touch devices
    const hoverElements = document.querySelectorAll('.benefit-card, .solution-card, .business-type-card, .partner-logo');
    hoverElements.forEach(element => {
        element.addEventListener('touchstart', function() {
            this.classList.add('touch-hover');
        });
        
        element.addEventListener('touchend', function() {
            setTimeout(() => {
                this.classList.remove('touch-hover');
            }, 300);
        });
    });
}

// Preload images for better performance
function preloadImages() {
    const imageUrls = [
        'https://stc-zaloprofile.zdn.vn/pc/v1/images/logo_zalopay.png',
        'https://stc-zaloprofile.zdn.vn/pc/v1/images/logo_zalopay_white.png',
        'https://scdn.zalopay.com.vn/merchant-web/homepage/imgs/carousel/carousel-nha-hang.svg',
        'https://scdn.zalopay.com.vn/merchant-web/homepage/imgs/carousel/carousel-ban-le.svg',
        'https://scdn.zalopay.com.vn/merchant-web/homepage/imgs/carousel/carousel-dvcn.svg'
    ];
    
    imageUrls.forEach(url => {
        const img = new Image();
        img.src = url;
    });
}

// Initialize preloading when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', preloadImages);
} else {
    preloadImages();
}

// Export functions for global use if needed
window.ZaloPayMerchant = {
    showLoading,
    hideLoading,
    trackEvent,
    debounce,
    throttle
};
