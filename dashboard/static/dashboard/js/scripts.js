// Modern Interactive Dashboard with Smooth Animations
document.addEventListener('DOMContentLoaded', function() {
    // Enhanced mobile menu with smooth animations
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');

    if (mobileMenuToggle && sidebar && mainContent) {
        mobileMenuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            sidebar.classList.toggle('active');
            mainContent.classList.toggle('sidebar-active');
        });

        document.addEventListener('click', function(event) {
            const isClickInside = mobileMenuToggle.contains(event.target) || sidebar.contains(event.target);
            if (!isClickInside && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                mainContent.classList.remove('sidebar-active');
            }
        });

        sidebar.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                sidebar.classList.remove('active');
                mainContent.classList.remove('sidebar-active');
            }
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Enhanced button interactions with ripple effect
    document.querySelectorAll('.btn, .export-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple-effect');

            this.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Card hover animations with stagger effect
    const cards = document.querySelectorAll('.card, .stat-card, .export-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;

        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Form enhancement with loading states
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
            const isGetForm = !form.method || form.method.toLowerCase() === 'get';
            const isExportForm = form.classList.contains('export-form') ||
                                 (form.action && (form.action.includes('/export/csv') || form.action.includes('/export/pdf')));

            if (isGetForm || isExportForm) {
                submitButtons.forEach(button => {
                    const originalText = button.innerHTML;
                    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                    button.disabled = true;

                    // Re-enable after a short delay for export forms
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.disabled = false;
                    }, 2000);
                });
            }
        });
    });

    // Input focus animations
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });

    // Navigation link active state with smooth transitions
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(8px)';
        });

        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });

    // Stat card number animation
    const statNumbers = document.querySelectorAll('.stat-content h3');
    statNumbers.forEach(stat => {
        const target = parseFloat(stat.textContent.replace(/[^\d.]/g, ''));
        if (!isNaN(target)) {
            animateNumber(stat, 0, target, 1000);
        }
    });

    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .stat-card, .export-card, .chart-container').forEach(el => {
        observer.observe(el);
    });

    // Dynamic theme switching (optional)
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            const icon = this.querySelector('i');
            if (document.body.classList.contains('dark-theme')) {
                icon.className = 'fas fa-sun';
            } else {
                icon.className = 'fas fa-moon';
            }
        });
    }
});

// Number animation function
function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    const endTime = startTime + duration;

    function update(currentTime) {
        if (currentTime >= endTime) {
            element.textContent = element.textContent.replace(/\d+(\.\d+)?/, end.toFixed(2));
            return;
        }

        const progress = (currentTime - startTime) / duration;
        const current = start + (end - start) * easeOutCubic(progress);

        element.textContent = element.textContent.replace(/\d+(\.\d+)?/, current.toFixed(2));
        requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
}

// Easing function for smooth animations
function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

// Add ripple effect styles dynamically
const style = document.createElement('style');
style.textContent = `
    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple 0.6s linear;
        pointer-events: none;
    }

    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }

    .animate-in {
        animation: fadeInUp 0.6s ease-out forwards;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

document.addEventListener('DOMContentLoaded', function() {
    const tableRows = document.querySelectorAll('table tbody tr');

    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.03) translateX(5px)';
            this.style.transition = 'all 0.3s ease';
            this.style.boxShadow = '0 4px 15px rgba(37, 99, 235, 0.3)';
        });

        row.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) translateX(0)';
            this.style.boxShadow = 'none';
        });
    });
});

// Alert auto-dismiss functionality
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(alert => {
        // Auto-dismiss success and info alerts after 5 seconds
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(() => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                alert.style.transition = 'all 0.3s ease';

                setTimeout(() => {
                    alert.remove();
                }, 300);
            }, 5000);
        }

        // Add close button to all alerts
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '<i class="fas fa-times"></i>';
        closeButton.style.background = 'none';
        closeButton.style.border = 'none';
        closeButton.style.cursor = 'pointer';
        closeButton.style.fontSize = '0.875rem';
        closeButton.style.opacity = '0.7';
        closeButton.style.marginLeft = 'auto';
        closeButton.style.padding = '0';

        closeButton.addEventListener('click', function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            alert.style.transition = 'all 0.3s ease';

            setTimeout(() => {
                alert.remove();
            }, 300);
        });

        alert.appendChild(closeButton);
    });
});

// Enhanced navigation performance - Optimized dropdowns
document.addEventListener('DOMContentLoaded', function() {
    const dropdowns = document.querySelectorAll('.nav-item.dropdown');
    let activeDropdown = null;

    // Pre-calculate dropdown elements for performance
    const dropdownData = Array.from(dropdowns).map(dropdown => ({
        element: dropdown,
        link: dropdown.querySelector('.nav-link'),
        menu: dropdown.querySelector('.dropdown-menu'),
        isActive: false
    }));

    // Fast dropdown toggle with optimized event handling
    dropdownData.forEach(data => {
        const { element, link, menu } = data;

        link.addEventListener('click', function(e) {
            if (this.getAttribute('href') !== '#') return;

            e.preventDefault();
            
            // Fast close all other dropdowns
            dropdownData.forEach(other => {
                if (other !== data && other.isActive) {
                    other.element.classList.remove('active');
                    other.menu.style.opacity = '0';
                    other.menu.style.visibility = 'hidden';
                    other.menu.style.pointerEvents = 'none';
                    other.isActive = false;
                }
            });

            // Toggle current dropdown with immediate feedback
            data.isActive = !data.isActive;
            element.classList.toggle('active', data.isActive);
            
            if (data.isActive) {
                menu.style.opacity = '1';
                menu.style.visibility = 'visible';
                menu.style.pointerEvents = 'auto';
                activeDropdown = element;
            } else {
                menu.style.opacity = '0';
                menu.style.visibility = 'hidden';
                menu.style.pointerEvents = 'none';
                activeDropdown = null;
            }
        });
    });

    // Optimized document click handler
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.nav-item.dropdown')) {
            dropdownData.forEach(data => {
                if (data.isActive) {
                    data.element.classList.remove('active');
                    data.menu.style.opacity = '0';
                    data.menu.style.visibility = 'hidden';
                    data.menu.style.pointerEvents = 'none';
                    data.isActive = false;
                }
            });
            activeDropdown = null;
        }
    });

    // User menu optimization
    const userMenuToggle = document.querySelector('.user-menu-toggle');
    const userMenuDropdown = document.querySelector('.user-menu-dropdown');
    
    if (userMenuToggle && userMenuDropdown) {
        userMenuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            userMenuDropdown.classList.toggle('active');
        });
        
        document.addEventListener('click', function() {
            userMenuDropdown.classList.remove('active');
        });
    }
});

// Theme toggle functionality - Optimized
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.querySelector('.theme-toggle');
    const body = document.body;

    // Check for saved theme preference or default to light mode
    const currentTheme = localStorage.getItem('theme') || 'light';
    body.setAttribute('data-theme', currentTheme);

    // Update icon based on current theme
    updateThemeIcon(currentTheme);

    themeToggle.addEventListener('click', function() {
        const currentTheme = body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);

        // Add smooth transition
        body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            body.style.transition = '';
        }, 300);
    });

    function updateThemeIcon(theme) {
        const icon = themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
        } else {
            icon.className = 'fas fa-moon';
        }
    }
});

// Search and filter for Appliances and Usage Records tables
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    if (!container) return;

    // Add search input dynamically to Appliances and Usage Records pages
    if (window.location.pathname.includes('/appliances/') || window.location.pathname.includes('/usage_records/')) {
        const table = container.querySelector('table');
        if (!table) return;

        const searchDiv = document.createElement('div');
        searchDiv.style.marginBottom = '1rem';

        const searchLabel = document.createElement('label');
        searchLabel.textContent = 'Search: ';
        searchLabel.setAttribute('for', 'searchInput');
        searchDiv.appendChild(searchLabel);

        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.id = 'searchInput';
        searchInput.placeholder = 'Type to filter...';
        searchInput.style.padding = '0.3rem';
        searchInput.style.width = '200px';
        searchDiv.appendChild(searchInput);

        container.insertBefore(searchDiv, table);

        searchInput.addEventListener('input', function() {
            const filter = searchInput.value.toLowerCase();
            const rows = table.tBodies[0].rows;
            for (let row of rows) {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            }
        });
    }
});

// Table sorting for Appliances and Usage Records tables
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    if (!container) return;

    if (window.location.pathname.includes('/appliances/') || window.location.pathname.includes('/usage_records/')) {
        const tables = container.querySelectorAll('table');
        tables.forEach(function(table) {
            makeTableSortable(table);
        });
    }

    function makeTableSortable(table) {
        const headers = table.tHead.rows[0].cells;
        for (let i = 0; i < headers.length; i++) {
            headers[i].style.cursor = 'pointer';
            headers[i].addEventListener('click', function() {
                sortTableByColumn(table, i);
            });
        }
    }

    function sortTableByColumn(table, columnIndex) {
        const tbody = table.tBodies[0];
        const rows = Array.from(tbody.rows);
        const isNumeric = !isNaN(rows[0].cells[columnIndex].textContent.trim());
        const currentIsAsc = table.getAttribute('data-sort-dir') === 'asc';
        rows.sort(function(a, b) {
            let aText = a.cells[columnIndex].textContent.trim();
            let bText = b.cells[columnIndex].textContent.trim();
            if (isNumeric) {
                aText = parseFloat(aText);
                bText = parseFloat(bText);
            }
            if (aText < bText) return currentIsAsc ? 1 : -1;
            if (aText > bText) return currentIsAsc ? -1 : 1;
            return 0;
        });
        rows.forEach(function(row) {
            tbody.appendChild(row);
        });
        table.setAttribute('data-sort-dir', currentIsAsc ? 'desc' : 'asc');
    }
});

// Client-side form validation for Add Appliance and Add Usage Record forms
document.addEventListener('DOMContentLoaded', function() {
    const addApplianceForm = document.querySelector('form:has(input[name="name"])');
    const addUsageForm = document.querySelector('form:has(input[name="date"])');

    if (addApplianceForm) {
        addApplianceForm.addEventListener('submit', function(e) {
            const powerInput = addApplianceForm.querySelector('input[name="power_rating"]');
            if (powerInput && (isNaN(powerInput.value) || powerInput.value <= 0)) {
                e.preventDefault();
                alert('Please enter a valid positive number for Power Rating.');
                powerInput.focus();
            }
        });
    }

    if (addUsageForm) {
        addUsageForm.addEventListener('submit', function(e) {
            const hoursInput = addUsageForm.querySelector('input[name="hours_used"]');
            const dateInput = addUsageForm.querySelector('input[name="date"]');
            if (hoursInput && (isNaN(hoursInput.value) || hoursInput.value <= 0)) {
                e.preventDefault();
                alert('Please enter a valid positive number for Hours Used.');
                hoursInput.focus();
            }
            if (dateInput && !dateInput.value) {
                e.preventDefault();
                alert('Please select a valid date.');
                dateInput.focus();
            }
        });
    }
});

// AJAX SMS handler for High Usage Dashboard (enhanced)
// AJAX form submissions for Add Appliance and Add Usage Record forms
document.addEventListener('DOMContentLoaded', function() {
    // High Usage SMS AJAX
    document.querySelectorAll('.send-sms-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const btn = this.querySelector('.send-sms-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Sending...';
            btn.disabled = true;
            
            fetch(this.action, {
                method: 'POST',
                body: new FormData(this),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    btn.innerHTML = '<i class="fas fa-check-circle text-success me-1"></i>Sent!';
                    btn.classList.add('btn-success');
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                    }, 3000);
                } else {
                    btn.innerHTML = '<i class="fas fa-times-circle text-danger me-1"></i>Error';
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                    }, 2000);
                }
            })
            .catch(() => {
                btn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }, 2000);
            });
        });
    });
    
    // Existing form handlers...
    const forms = document.querySelectorAll('form[method="post"]:not(.send-sms-form)');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const url = form.action || window.location.href;
            const formData = new FormData(form);
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(function(response) {
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    return response.text();
                }
            })
            .then(function(data) {
                if (data) {
                    alert('Form submitted successfully.');
                }
            })
            .catch(function() {
                alert('An error occurred while submitting the form.');
            });
        });
    });
});

// Enhanced delete confirmations with custom modals
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('a.btn-danger');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to delete this item?')) {
                window.location.href = button.href;
            }
        });
    });
});

// Tooltips on buttons and table rows
document.addEventListener('DOMContentLoaded', function() {
    const tooltipElements = document.querySelectorAll('a.btn, button, th, td');
    tooltipElements.forEach(function(el) {
        el.setAttribute('title', el.textContent.trim());
    });
});

// Placeholder for live data updates (polling every 60 seconds)
setInterval(function() {
    // Implement AJAX polling to refresh data if backend supports it
    console.log('Polling for live data updates...');
}, 60000);

// Pagination with AJAX for tables with many rows
document.addEventListener('DOMContentLoaded', function() {
    const tables = document.querySelectorAll('table');
    tables.forEach(function(table) {
        const rowsPerPage = 10;
        const tbody = table.tBodies[0];
        const rows = Array.from(tbody.rows);
        if (rows.length <= rowsPerPage) return;

        let currentPage = 1;
        const totalPages = Math.ceil(rows.length / rowsPerPage);

        const paginationDiv = document.createElement('div');
        paginationDiv.className = 'pagination-controls';
        paginationDiv.style.marginTop = '1rem';

        function renderPage(page) {
            currentPage = page;
            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            rows.forEach(function(row, index) {
                row.style.display = (index >= start && index < end) ? '' : 'none';
            });
            renderPagination();
        }

        function renderPagination() {
            paginationDiv.innerHTML = '';
            for (let i = 1; i <= totalPages; i++) {
                const btn = document.createElement('button');
                btn.textContent = i;
                btn.className = (i === currentPage) ? 'active' : '';
                btn.addEventListener('click', function() {
                    renderPage(i);
                });
                paginationDiv.appendChild(btn);
            }
        }

        table.parentNode.insertBefore(paginationDiv, table.nextSibling);
        renderPage(1);
    });
});

// Appliance search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('applianceSearch');
    const appliancesTable = document.getElementById('appliancesTable');

    if (searchInput && appliancesTable) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = appliancesTable.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const shouldShow = text.includes(searchTerm);
                row.style.display = shouldShow ? '' : 'none';
            });
        });
    }
});

// Loading state management
function showLoading() {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = '<div class="loading-spinner"></div>';
    loadingOverlay.id = 'loadingOverlay';
    document.body.appendChild(loadingOverlay);
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

// Enhanced form validation
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form[data-validate="true"]');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('error');
                    isValid = false;
                } else {
                    field.classList.remove('error');
                }
            });

            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields', 'error');
            }
        });
    });
});

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        ${message}
        <button class="alert-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    const container = document.querySelector('.page-content') || document.body;
    container.insertBefore(notification, container.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Automatic usage alerts checking
function checkUsageAlerts() {
    if (confirm('Check electricity usage for all residents and send automatic alerts to those with high consumption?')) {
        // Show loading state
        const button = event.target.closest('.action-item');
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Checking...</span>';
        button.disabled = true;

        fetch('/dashboard/check_usage_alerts/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            // Restore button
            button.innerHTML = originalHTML;
            button.disabled = false;

            if (data.success) {
                let message = data.message;

                // Show detailed breakdown if alerts were sent
                if (data.alerts_sent > 0 && data.high_usage_residents) {
                    message += '\n\nAlert Details:';
                    data.high_usage_residents.forEach(function(resident) {
                        const status = resident.email_failed ? ' (Email failed)' : ' (Email sent)';
                        message += `\n• ${resident.name}: ${resident.usage} kWh (MUR ${resident.cost})${status}`;
                    });
                }

                alert(message);

                // Reload page to show any new alerts in the dashboard
                if (data.alerts_sent > 0) {
                    location.reload();
                }
            } else {
                alert('Failed to check alerts: ' + data.message);
            }
        })
        .catch(function(error) {
            // Restore button
            button.innerHTML = originalHTML;
            button.disabled = false;
            alert('Error checking usage alerts. Please check your email configuration.');
        });
    }
}
