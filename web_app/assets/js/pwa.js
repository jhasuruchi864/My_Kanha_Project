// PWA Registration and Install Prompt Handler
(function() {
  'use strict';

  // Store the deferred install prompt
  let deferredPrompt = null;
  let isInstalled = false;

  // Check if app is already installed
  function checkIfInstalled() {
    // Check display-mode
    if (window.matchMedia('(display-mode: standalone)').matches) {
      isInstalled = true;
      return true;
    }

    // Check iOS standalone mode
    if (window.navigator.standalone === true) {
      isInstalled = true;
      return true;
    }

    return false;
  }

  // Register Service Worker
  async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      console.log('[PWA] Service Workers not supported');
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });

      console.log('[PWA] Service Worker registered:', registration.scope);

      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        console.log('[PWA] New Service Worker installing...');

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New content available
            showUpdateNotification();
          }
        });
      });

      return registration;
    } catch (error) {
      console.error('[PWA] Service Worker registration failed:', error);
      return null;
    }
  }

  // Show update notification
  function showUpdateNotification() {
    // Create a simple notification banner
    const banner = document.createElement('div');
    banner.id = 'pwa-update-banner';
    banner.innerHTML = `
      <div class="pwa-update-content">
        <span>A new version is available!</span>
        <button onclick="window.location.reload()">Update</button>
        <button onclick="this.parentElement.parentElement.remove()">Later</button>
      </div>
    `;
    banner.style.cssText = `
      position: fixed;
      bottom: 80px;
      left: 50%;
      transform: translateX(-50%);
      background: linear-gradient(135deg, #e09f3e, #b6893e);
      color: white;
      padding: 12px 20px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
      z-index: 10001;
      font-family: 'Segoe UI', Arial, sans-serif;
      animation: slideUp 0.3s ease-out;
    `;

    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideUp {
        from { transform: translateX(-50%) translateY(100px); opacity: 0; }
        to { transform: translateX(-50%) translateY(0); opacity: 1; }
      }
      #pwa-update-banner .pwa-update-content {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      #pwa-update-banner button {
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.3);
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        transition: background 0.2s;
      }
      #pwa-update-banner button:hover {
        background: rgba(255,255,255,0.3);
      }
    `;
    document.head.appendChild(style);
    document.body.appendChild(banner);
  }

  // Handle beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] beforeinstallprompt fired');

    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();

    // Store the event for later use
    deferredPrompt = e;

    // Show install button if it exists
    showInstallButton();
  });

  // Show install button
  function showInstallButton() {
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.style.display = 'flex';
      installBtn.classList.add('pwa-install-available');
    }
  }

  // Hide install button
  function hideInstallButton() {
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.style.display = 'none';
      installBtn.classList.remove('pwa-install-available');
    }
  }

  // Trigger install prompt
  async function promptInstall() {
    if (!deferredPrompt) {
      console.log('[PWA] No install prompt available');

      // Show manual instructions for iOS
      if (isIOS()) {
        showIOSInstallInstructions();
      }
      return false;
    }

    // Show the prompt
    deferredPrompt.prompt();

    // Wait for user response
    const { outcome } = await deferredPrompt.userChoice;
    console.log('[PWA] User response:', outcome);

    // Clear the deferred prompt
    deferredPrompt = null;

    if (outcome === 'accepted') {
      console.log('[PWA] User accepted install prompt');
      hideInstallButton();
      return true;
    }

    return false;
  }

  // Check if iOS
  function isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  }

  // Show iOS install instructions
  function showIOSInstallInstructions() {
    const modal = document.createElement('div');
    modal.id = 'ios-install-modal';
    modal.innerHTML = `
      <div class="ios-install-overlay" onclick="this.parentElement.remove()"></div>
      <div class="ios-install-content">
        <h3>Install My Kanha</h3>
        <p>To install this app on your iPhone/iPad:</p>
        <ol>
          <li>Tap the Share button <span style="font-size: 1.2em;">&#x1F4E4;</span></li>
          <li>Scroll down and tap "Add to Home Screen"</li>
          <li>Tap "Add" in the top right</li>
        </ol>
        <button onclick="this.closest('#ios-install-modal').remove()">Got it</button>
      </div>
    `;
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 10002;
      display: flex;
      align-items: center;
      justify-content: center;
    `;

    const style = document.createElement('style');
    style.textContent = `
      #ios-install-modal .ios-install-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
      }
      #ios-install-modal .ios-install-content {
        position: relative;
        background: #fffbe6;
        padding: 24px;
        border-radius: 16px;
        max-width: 320px;
        margin: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        font-family: 'Segoe UI', Arial, sans-serif;
      }
      #ios-install-modal h3 {
        color: #b6893e;
        margin: 0 0 12px 0;
        font-size: 1.3rem;
      }
      #ios-install-modal p {
        color: #7c6f57;
        margin: 0 0 16px 0;
      }
      #ios-install-modal ol {
        color: #7c6f57;
        padding-left: 20px;
        margin: 0 0 20px 0;
      }
      #ios-install-modal li {
        margin-bottom: 8px;
      }
      #ios-install-modal button {
        width: 100%;
        background: linear-gradient(90deg, #e09f3e, #b6e2d3);
        color: white;
        border: none;
        padding: 12px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
      }
    `;
    document.head.appendChild(style);
    document.body.appendChild(modal);
  }

  // Handle app installed event
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App was installed');
    isInstalled = true;
    deferredPrompt = null;
    hideInstallButton();
  });

  // Initialize PWA
  function initPWA() {
    checkIfInstalled();

    // Register service worker
    registerServiceWorker();

    // If already installed, hide install button
    if (isInstalled) {
      hideInstallButton();
    }
  }

  // Expose functions globally
  window.PWA = {
    install: promptInstall,
    isInstalled: () => isInstalled,
    checkIfInstalled: checkIfInstalled
  };

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPWA);
  } else {
    initPWA();
  }
})();
