// Settings management for dark mode and color themes
const SETTINGS_KEY = 'kanha_settings';

// Default color themes - Modern & Stylish
const COLOR_THEMES = {
    default: {
        name: 'Warm Sunset',
        primary: '#ffb74d',
        secondary: '#ffe0b2',
        accent: '#ffa726',
        background: '#ffffff',
        text: '#000000',
        darkBackground: '#0f0f1e',
        darkText: '#e0e0e0'
    },
    green: {
        name: 'Emerald Dream',
        primary: '#26c6da',
        secondary: '#4dd0e1',
        accent: '#00acc1',
        background: '#ffffff',
        text: '#000000',
        darkBackground: '#0f0f1e',
        darkText: '#e0e0e0'
    },
    purple: {
        name: 'Royal Violet',
        primary: '#ab47bc',
        secondary: '#ba68c8',
        accent: '#9c27b0',
        background: '#ffffff',
        text: '#000000',
        darkBackground: '#0f0f1e',
        darkText: '#e0e0e0'
    },
    orange: {
        name: 'Vibrant Coral',
        primary: '#ff7043',
        secondary: '#ff8a65',
        accent: '#ff6e40',
        background: '#ffffff',
        text: '#000000',
        darkBackground: '#0f0f1e',
        darkText: '#e0e0e0'
    },
    red: {
        name: 'Rose Glow',
        primary: '#e91e63',
        secondary: '#f48fb1',
        accent: '#ec407a',
        background: '#ffffff',
        text: '#000000',
        darkBackground: '#0f0f1e',
        darkText: '#e0e0e0'
    },
    teal: {
        name: 'Ocean Breeze',
        primary: '#0097a7',
        secondary: '#00bcd4',
        accent: '#0288d1',
        background: '#ffffff',
        text: '#000000',
        darkBackground: '#0f0f1e',
        darkText: '#e0e0e0'
    }
};

// Initialize settings on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    setupEventListeners();
    applyTheme();
});

/**
 * Load settings from localStorage
 */
function loadSettings() {
    try {
        const saved = localStorage.getItem(SETTINGS_KEY);
        if (saved) {
            return JSON.parse(saved);
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
    return getDefaultSettings();
}

/**
 * Get default settings
 */
function getDefaultSettings() {
    return {
        darkMode: false,
        colorTheme: 'default',
        language: 'en'
    };
}

/**
 * Save settings to localStorage
 */
function saveSettings(settings) {
    try {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
        console.log('Settings saved:', settings);
        return true;
    } catch (error) {
        console.error('Error saving settings:', error);
        return false;
    }
}

/**
 * Setup event listeners for form controls
 */
function setupEventListeners() {
    const darkModeToggle = document.getElementById('darkMode');
    const colorThemeSelect = document.getElementById('colorTheme');
    const settingsForm = document.querySelector('.settings-form');

    if (darkModeToggle) {
        const settings = loadSettings();
        darkModeToggle.checked = settings.darkMode;
        updateDarkModeStatus();

        darkModeToggle.addEventListener('change', function() {
            updateDarkModeStatus();
            applyTheme();
        });
    }

    if (colorThemeSelect) {
        const settings = loadSettings();
        colorThemeSelect.value = settings.colorTheme;

        colorThemeSelect.addEventListener('change', function() {
            applyTheme();
            updatePreview();
        });
    }

    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleSettingsSave();
        });

        settingsForm.addEventListener('reset', function(e) {
            setTimeout(() => {
                resetSettings();
            }, 0);
        });
    }
}

/**
 * Update dark mode status display
 */
function updateDarkModeStatus() {
    const toggle = document.getElementById('darkMode');
    const statusText = document.getElementById('darkModeStatus');
    if (statusText) {
        statusText.textContent = toggle.checked ? 'On' : 'Off';
    }
}

/**
 * Apply theme to the document
 */
function applyTheme() {
    const settings = {
        darkMode: document.getElementById('darkMode')?.checked || false,
        colorTheme: document.getElementById('colorTheme')?.value || 'default'
    };

    const theme = COLOR_THEMES[settings.colorTheme] || COLOR_THEMES.default;
    const root = document.documentElement;

    // Set CSS variables for color theme
    root.style.setProperty('--primary-color', theme.primary);
    root.style.setProperty('--secondary-color', theme.secondary);
    root.style.setProperty('--accent-color', theme.accent);

    // Set dark mode styles
    if (settings.darkMode) {
        document.body.classList.add('dark-mode');
        root.style.setProperty('--bg-color', theme.darkBackground);
        root.style.setProperty('--text-color', theme.darkText);
    } else {
        document.body.classList.remove('dark-mode');
        root.style.setProperty('--bg-color', theme.background);
        root.style.setProperty('--text-color', theme.text);
    }

    updatePreview();
}

/**
 * Update theme preview
 */
function updatePreview() {
    const colorTheme = document.getElementById('colorTheme')?.value || 'default';
    const theme = COLOR_THEMES[colorTheme] || COLOR_THEMES.default;
    const previewBoxes = document.querySelectorAll('.preview-box');

    if (previewBoxes.length >= 3) {
        previewBoxes[0].style.backgroundColor = theme.primary;
        previewBoxes[1].style.backgroundColor = theme.secondary;
        previewBoxes[2].style.backgroundColor = theme.accent;
    }
}

/**
 * Handle settings form submission
 */
function handleSettingsSave() {
    const settings = {
        darkMode: document.getElementById('darkMode')?.checked || false,
        colorTheme: document.getElementById('colorTheme')?.value || 'default',
        language: document.getElementById('language')?.value || 'en'
    };

    if (saveSettings(settings)) {
        applyTheme();
        showNotification('Settings saved successfully!', 'success');
    } else {
        showNotification('Error saving settings', 'error');
    }
}

/**
 * Reset settings to default
 */
function resetSettings() {
    const defaults = getDefaultSettings();
    
    if (document.getElementById('darkMode')) {
        document.getElementById('darkMode').checked = defaults.darkMode;
        updateDarkModeStatus();
    }
    
    if (document.getElementById('colorTheme')) {
        document.getElementById('colorTheme').value = defaults.colorTheme;
    }
    
    if (document.getElementById('language')) {
        document.getElementById('language').value = defaults.language;
    }

    saveSettings(defaults);
    applyTheme();
    showNotification('Settings reset to default', 'info');
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background-color: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: slideIn 0.3s ease-in-out;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Initialize theme on page load
 */
function initializeTheme() {
    const settings = loadSettings();
    
    // Apply dark mode class
    if (settings.darkMode) {
        document.documentElement.classList.add('dark-mode');
        document.body.classList.add('dark-mode');
    } else {
        document.documentElement.classList.remove('dark-mode');
        document.body.classList.remove('dark-mode');
    }
    
    // Apply color theme
    const theme = COLOR_THEMES[settings.colorTheme] || COLOR_THEMES.default;
    const root = document.documentElement;
    
    root.style.setProperty('--primary-color', theme.primary);
    root.style.setProperty('--secondary-color', theme.secondary);
    root.style.setProperty('--accent-color', theme.accent);
    root.style.setProperty('--bg-color', settings.darkMode ? theme.darkBackground : theme.background);
    root.style.setProperty('--text-color', settings.darkMode ? theme.darkText : theme.text);
}

// Initialize theme immediately when script loads
initializeTheme();

// Also watch for storage changes from other tabs
window.addEventListener('storage', function(e) {
    if (e.key === SETTINGS_KEY) {
        initializeTheme();
    }
});
