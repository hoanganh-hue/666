// ZaloPay Admin Portal JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeAdminPortal();
});

function initializeAdminPortal() {
    // Initialize theme
    initializeTheme();
    
    // Initialize sidebar
    initializeSidebar();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize charts if on dashboard
    if (document.getElementById('registrationChart')) {
        initializeDashboardCharts();
    }
    
    // Initialize data tables
    initializeDataTables();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize AJAX handlers
    initializeAjaxHandlers();
    
    // Set moment locale
    if (typeof moment !== 'undefined') {
        moment.locale('vi');
    }
}

// Theme Management
function initializeTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    
    // Load saved theme
    const savedTheme = localStorage.getItem('admin-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('admin-theme', newTheme);
            updateThemeIcon(newTheme);
            
            // Animate the transition
            document.body.style.transition = 'all 0.3s ease';
            setTimeout(() => {
                document.body.style.transition = '';
            }, 300);
        });
    }
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Sidebar Management
function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('show');
            } else {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
            }
        });
    }
    
    // Handle responsive sidebar
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('show');
        } else {
            sidebar.classList.remove('show');
        }
    });
    
    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && 
            sidebar && !sidebar.contains(e.target) && 
            sidebarToggle && !sidebarToggle.contains(e.target) &&
            sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
        }
    });
}

// Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Dashboard Charts
function initializeDashboardCharts() {
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.color = '#6c757d';
    
    // Registration Chart
    const registrationCtx = document.getElementById('registrationChart');
    if (registrationCtx && typeof registrationData !== 'undefined') {
        new Chart(registrationCtx, {
            type: 'line',
            data: {
                labels: registrationData.map(item => {
                    const date = new Date(item.date);
                    return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
                }),
                datasets: [{
                    label: 'Đăng ký mới',
                    data: registrationData.map(item => item.count),
                    borderColor: '#0068FF',
                    backgroundColor: 'rgba(0, 104, 255, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#0068FF',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#0068FF',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        border: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                return Number.isInteger(value) ? value : '';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        border: {
                            display: false
                        }
                    }
                }
            }
        });
    }
    
    // Industry Chart
    const industryCtx = document.getElementById('industryChart');
    if (industryCtx && typeof industryData !== 'undefined') {
        const industryLabels = {
            'restaurant': 'Nhà hàng',
            'retail': 'Bán lẻ', 
            'services': 'Dịch vụ',
            'entertainment': 'Giải trí',
            'online': 'Online',
            'canteen': 'Căn tin',
            'parking': 'Bãi đỗ xe',
            'other': 'Khác'
        };
        
        new Chart(industryCtx, {
            type: 'doughnut',
            data: {
                labels: industryData.map(item => industryLabels[item.industry] || item.industry),
                datasets: [{
                    data: industryData.map(item => item.count),
                    backgroundColor: [
                        '#0068FF', '#28a745', '#ffc107', '#dc3545',
                        '#6f42c1', '#fd7e14', '#20c997', '#6c757d'
                    ],
                    borderWidth: 0,
                    hoverBorderWidth: 2,
                    hoverBorderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#0068FF',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed * 100) / total).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }
}

// Data Tables
function initializeDataTables() {
    // Initialize DataTables if jQuery is available
    if (typeof $ !== 'undefined' && $.fn.DataTable) {
        $('.data-table').DataTable({
            pageLength: 25,
            responsive: true,
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/vi.json'
            },
            dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                 '<"row"<"col-sm-12"tr>>' +
                 '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
            drawCallback: function() {
                // Reinitialize tooltips after table redraw
                initializeTooltips();
            }
        });
    }
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Show first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Real-time validation
    const inputs = document.querySelectorAll('.form-control, .form-select');
    inputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.checkValidity()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid') && this.checkValidity()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    });
}

// AJAX Handlers
function initializeAjaxHandlers() {
    // Set CSRF token for all AJAX requests
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken.getAttribute('content'));
                }
            }
        });
    }
    
    // Global AJAX error handler
    $(document).ajaxError(function(event, xhr, settings, thrownError) {
        console.error('AJAX Error:', thrownError);
        
        let message = 'Có lỗi xảy ra khi xử lý yêu cầu.';
        if (xhr.status === 403) {
            message = 'Bạn không có quyền thực hiện hành động này.';
        } else if (xhr.status === 404) {
            message = 'Không tìm thấy tài nguyên yêu cầu.';
        } else if (xhr.status === 500) {
            message = 'Lỗi hệ thống. Vui lòng thử lại sau.';
        }
        
        showAlert(message, 'error');
    });
}

// Utility Functions
function showAlert(message, type = 'info', duration = 5000) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: type === 'error' ? 'Lỗi' : type === 'success' ? 'Thành công' : 'Thông báo',
            text: message,
            icon: type === 'error' ? 'error' : type === 'success' ? 'success' : 'info',
            timer: duration,
            showConfirmButton: false,
            toast: true,
            position: 'top-end'
        });
    } else {
        // Fallback to browser alert
        alert(message);
    }
}

function confirmAction(message, callback) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Xác nhận',
            text: message,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#0068FF',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Xác nhận',
            cancelButtonText: 'Hủy'
        }).then((result) => {
            if (result.isConfirmed && callback) {
                callback();
            }
        });
    } else {
        if (confirm(message) && callback) {
            callback();
        }
    }
}

function showLoading(element) {
    if (element) {
        element.classList.add('loading');
        const originalContent = element.innerHTML;
        element.setAttribute('data-original-content', originalContent);
        
        if (element.tagName === 'BUTTON') {
            element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang xử lý...';
            element.disabled = true;
        }
    }
}

function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
        const originalContent = element.getAttribute('data-original-content');
        if (originalContent) {
            element.innerHTML = originalContent;
            element.removeAttribute('data-original-content');
        }
        
        if (element.tagName === 'BUTTON') {
            element.disabled = false;
        }
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// API Helper Functions
function apiCall(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const config = { ...defaultOptions, ...options };
    
    return fetch(url, config)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('API call error:', error);
            throw error;
        });
}

// Export functions for global use
window.AdminPortal = {
    showAlert,
    confirmAction,
    showLoading,
    hideLoading,
    formatCurrency,
    formatDate,
    debounce,
    apiCall
};

// Dashboard specific functions
function updateDashboard() {
    const days = document.getElementById('dateRange')?.value || 30;
    window.location.href = `${window.location.pathname}?days=${days}`;
}

// Real-time updates (if WebSocket is available)
function initializeRealTimeUpdates() {
    // This would connect to WebSocket for real-time updates
    // Implementation depends on backend WebSocket setup
    console.log('Real-time updates initialized');
}

// Performance monitoring
function initializePerformanceMonitoring() {
    // Monitor page load times
    window.addEventListener('load', function() {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log('Page load time:', loadTime + 'ms');
        
        // Send to analytics if needed
        if (loadTime > 3000) {
            console.warn('Slow page load detected:', loadTime + 'ms');
        }
    });
}

// Initialize performance monitoring
initializePerformanceMonitoring();
