// Login Page JavaScript

// Exchange Firebase ID token with backend and store server JWT
async function exchangeFirebaseToken() {
  try {
    if (!window.Firebase || !window.Firebase.auth) {
      throw new Error('Firebase not initialized');
    }
    const idToken = await window.Firebase.getIdToken();
    if (!idToken) throw new Error('No Firebase ID token');

    const resp = await fetch('/auth/firebase', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: idToken })
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Auth failed' }));
      throw new Error(err.detail || 'Auth failed');
    }
    const data = await resp.json();
    if (data.access_token) {
      localStorage.setItem('authToken', data.access_token);
      if (data.user) localStorage.setItem('user', JSON.stringify(data.user));
      window.location.href = 'chat.html';
    } else {
      throw new Error('Missing access_token in response');
    }
  } catch (e) {
    console.error('Token exchange error:', e);
    showError(e.message || 'Authentication failed');
  }
}

// Handle form submission for email/password login
document.getElementById('loginForm').addEventListener('submit', async function(e) {
  e.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const loginBtn = document.querySelector('.login-btn');

  loginBtn.disabled = true;
  const originalText = loginBtn.textContent;
  loginBtn.textContent = 'Signing in...';

  try {
    if (!window.Firebase) throw new Error('Firebase not initialized');
    await window.Firebase.signInWithEmailAndPassword(window.Firebase.auth, email, password);
    await exchangeFirebaseToken();
    document.getElementById('loginForm').reset();
  } catch (error) {
    console.error('Email login error:', error);
    showError(error.message || 'Login failed. Please try again.');
    loginBtn.disabled = false;
    loginBtn.textContent = originalText;
  }
});

// Show error message
function showError(message) {
  // Create error element
  let errorDiv = document.querySelector('.error-message');
  
  if (!errorDiv) {
    errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    document.querySelector('.login-form').insertBefore(errorDiv, document.querySelector('.form-group'));
  }
  
  errorDiv.textContent = message;
  errorDiv.style.display = 'block';
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    errorDiv.style.display = 'none';
  }, 5000);
}

// Check if already logged in
window.addEventListener('DOMContentLoaded', function() {
  const authToken = localStorage.getItem('authToken');
  if (authToken) {
    // User is already logged in, redirect to chat
    window.location.href = 'chat.html';
  }
});

// Google Sign-In initialization
window.onload = function() {
  // Hook Google sign-in via Firebase popup
  const googleBtn = document.getElementById('googleSignInBtn');
  if (googleBtn) {
    googleBtn.addEventListener('click', async function(e) {
      e.preventDefault();
      try {
        await window.Firebase.signInWithPopup(window.Firebase.auth, window.Firebase.googleProvider);
        await exchangeFirebaseToken();
      } catch (err) {
        console.error('Google sign-in error:', err);
        showError('Google sign-in failed. Please try again.');
      }
    });
  }
};

// Add some CSS for error messages dynamically
const style = document.createElement('style');
style.textContent = `
  .error-message {
    display: none;
    padding: 0.9rem 1rem;
    margin-bottom: 1rem;
    background-color: #fee;
    border: 2px solid #f88;
    border-radius: 8px;
    color: #c33;
    font-weight: 500;
    font-size: 0.95rem;
    animation: slideDown 0.3s ease-out;
  }
  
  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;
document.head.appendChild(style);
