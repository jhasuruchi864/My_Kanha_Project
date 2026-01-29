// Signup Page JavaScript

// Detect if running on mobile device
function isMobileDevice() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Detect if running on localhost/local IP (development mode)
function isLocalDevelopment() {
  const hostname = window.location.hostname;
  return hostname === 'localhost' || 
         hostname === '127.0.0.1' || 
         hostname.startsWith('192.168.') || 
         hostname.startsWith('10.') ||
         hostname.startsWith('172.');
}

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

// Handle form submission for email/password signup
document.getElementById('signupForm').addEventListener('submit', async function(e) {
  e.preventDefault();

  const username = document.getElementById('username').value;
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const signupBtn = document.querySelector('.login-btn');

  signupBtn.disabled = true;
  const originalText = signupBtn.textContent;
  signupBtn.textContent = 'Creating account...';

  try {
    if (!window.Firebase) throw new Error('Firebase not initialized');

    // Step 1: Create user in Firebase Auth
    const userCredential = await window.Firebase.createUserWithEmailAndPassword(window.Firebase.auth, email, password);
    
    // Step 2: Register user on our backend
    const registerResponse = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: username,
            email: email,
            password: password,
            full_name: '' // Or some default, as we don't ask for it
        })
    });

    if (!registerResponse.ok) {
        const err = await registerResponse.json().catch(() => ({ detail: 'Registration failed on backend' }));
        throw new Error(err.detail || 'Backend registration failed');
    }

    const data = await registerResponse.json();
    
    // Step 3: Store token and redirect
    if (data.access_token) {
        localStorage.setItem('authToken', data.access_token);
        if (data.user) localStorage.setItem('user', JSON.stringify(data.user));
        window.location.href = 'chat.html';
    } else {
        throw new Error('Missing access_token in response');
    }

  } catch (error) {
    console.error('Signup error:', error);
    showError(error.message || 'Signup failed. Please try again.');
    signupBtn.disabled = false;
    signupBtn.textContent = originalText;
  }
});


// Show error message
function showError(message) {
  let errorDiv = document.querySelector('.error-message');
  
  if (!errorDiv) {
    errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    document.querySelector('.login-form').insertBefore(errorDiv, document.querySelector('.form-group'));
  }
  
  errorDiv.textContent = message;
  errorDiv.style.display = 'block';
  
  setTimeout(() => {
    errorDiv.style.display = 'none';
  }, 5000);
}

// Google Sign-In logic
window.onload = function() {
    const googleBtn = document.getElementById('googleSignInBtn');
    if (googleBtn) {
        googleBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            googleBtn.disabled = true;
            googleBtn.innerHTML = '<span style="display:flex;align-items:center;gap:8px;justify-content:center">Signing in...</span>';
            
            try {
                if (isMobileDevice() || isLocalDevelopment()) {
                    await window.Firebase.signInWithRedirect(window.Firebase.auth, window.Firebase.googleProvider);
                    return;
                }
                
                await window.Firebase.signInWithPopup(window.Firebase.auth, window.Firebase.googleProvider);
                await exchangeFirebaseToken();

            } catch (err) {
                console.error('Google sign-up error:', err);
                showError('Google sign-up failed. Please try again.');
                googleBtn.disabled = false;
                googleBtn.innerHTML = '<img src="assets/images/icon-192.png" alt="Google" style="width:20px;height:20px;border-radius:4px"> Sign up with Google';
            }
        });
    }

    // Also handle redirect result for Google Sign-In
    handleRedirectResult();
};

async function handleRedirectResult() {
    try {
        if (window.Firebase && window.Firebase.getRedirectResult) {
            const result = await window.Firebase.getRedirectResult(window.Firebase.auth);
            if (result && result.user) {
                await exchangeFirebaseToken();
            }
        }
    } catch (err) {
        console.error('Google redirect result error:', err);
    }
}
