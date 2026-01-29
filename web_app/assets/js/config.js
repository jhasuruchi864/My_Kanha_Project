/**
 * API Configuration
 * 
 * For LOCAL DEVELOPMENT/TESTING on mobile:
 * 1. Find your computer's local IP: run `ipconfig` in terminal
 * 2. Set API_BASE_URL to your IP, e.g., "http://10.149.213.138:8000"
 * 3. Make sure your backend is running
 * 4. Deploy to Firebase Hosting: firebase deploy --only hosting
 * 
 * For PRODUCTION:
 * - Set this to your deployed backend URL, or leave empty to use same origin
 */

// CHANGE THIS TO YOUR LOCAL IP FOR MOBILE TESTING
// Example: "http://10.149.213.138:8000" or "http://192.168.1.100:8000"
// Set to empty string "" for production (uses same origin)
window.API_BASE_URL = "http://10.149.213.138:8000";

// Uncomment the line below and set your local IP for mobile testing:
// window.API_BASE_URL = "http://10.149.213.138:8000";
