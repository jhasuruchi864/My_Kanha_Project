// Firebase initialization (ESM via CDN)
// This file must be loaded with type="module" in HTML.

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult, signInWithEmailAndPassword, createUserWithEmailAndPassword, onAuthStateChanged, signOut, sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-analytics.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCfJkTjQmUi1e-eSfgcYXC1Y_yDmhdNeTE",
  authDomain: "my-kanha.firebaseapp.com",
  projectId: "my-kanha",
  storageBucket: "my-kanha.firebasestorage.app",
  messagingSenderId: "73536646076",
  appId: "1:73536646076:web:2f96ad2a2d65bad41f99b9",
  measurementId: "G-NL7765JH07"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Expose minimal API on window for non-module scripts
window.Firebase = {
  app,
  analytics,
  auth,
  googleProvider,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signOut,
  sendPasswordResetEmail,
  async getIdToken() {
    const user = auth.currentUser;
    if (!user) return null;
    return await user.getIdToken();
  }
};

console.log("Firebase initialized", { projectId: firebaseConfig.projectId });
