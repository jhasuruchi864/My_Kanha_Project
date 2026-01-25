// Login Page JavaScript

// Handle Google Sign-In response
function handleCredentialResponse(response) {
  console.log('Encoded JWT ID token:', response.credential);
  
  // Send token to backend for verification
  fetch('/api/auth/google-login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      token: response.credential
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  })
  .then(data => {
    // Store the JWT token in localStorage
    if (data.access_token) {
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Redirect to chat page
      window.location.href = 'chat.html';
    } else {
      showError('Failed to authenticate with Google');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    showError('Google sign-in failed. Please try again.');
  });
}

// Handle form submission for email/password login
document.getElementById('loginForm').addEventListener('submit', function(e) {
  e.preventDefault();
  
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const loginBtn = document.querySelector('.login-btn');
  
  // Disable button and show loading state
  loginBtn.disabled = true;
  const originalText = loginBtn.textContent;
  loginBtn.textContent = 'Signing in...';
  
  // Send login request to backend
  fetch('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password
    })
  })
  .then(response => {
    if (!response.ok) {
      return response.json().then(data => {
        throw new Error(data.detail || 'Login failed');
      });
    }
    return response.json();
  })
  .then(data => {
    // Store the JWT token in localStorage
    if (data.access_token) {
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Clear form
      document.getElementById('loginForm').reset();
      
      // Redirect to chat page
      window.location.href = 'chat.html';
    } else {
      showError('Failed to retrieve authentication token');
      loginBtn.disabled = false;
      loginBtn.textContent = originalText;
    }
  })
  .catch(error => {
    console.error('Error:', error);
    showError(error.message || 'Login failed. Please check your credentials and try again.');
    loginBtn.disabled = false;
    loginBtn.textContent = originalText;
  });
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
  google.accounts.id.initialize({
    client_id: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com',
    callback: handleCredentialResponse,
    auto_select: false,
    itp_support: true
  });
  
  // Render the Google Sign-In button
  google.accounts.id.renderButton(
    document.querySelector('.g_id_signin'),
    {
      theme: 'outline',
      size: 'large',
      logo_alignment: 'left'
    }
  );
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
