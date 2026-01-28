// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyB9V6jbdF08wDA4MOtkcWSw6i036YVKi94",
  authDomain: "sankalp-chatbot.firebaseapp.com",
  projectId: "sankalp-chatbot",
  storageBucket: "sankalp-chatbot.firebasestorage.app",
  messagingSenderId: "132596670287",
  appId: "1:132596670287:web:ef94b7c40ecb196024af3a",
  measurementId: "G-2YPC9KMP6R"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);


