import { initializeApp } from "firebase/app";
import { getAuth, onAuthStateChanged, GoogleAuthProvider, signInWithPopup, signInAnonymously, signOut } from "firebase/auth";
import { getDatabase, ref, onDisconnect, set, onValue, push, serverTimestamp, goOffline, goOnline } from "firebase/database";
import { getFirestore, doc, setDoc, getDoc, persistentLocalCache, persistentMultipleTabManager, initializeFirestore } from "firebase/firestore";

const firebaseConfig = window.FIREBASE_CONFIG;
if (!firebaseConfig) {
    console.error("Firebase Config not found! Make sure .env is set and app.py is injecting it.");
}

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = initializeFirestore(app, {
    localCache: persistentLocalCache({ tabManager: persistentMultipleTabManager() })
});
const db_realtime = getDatabase(app); // Init RTDB
const googleProvider = new GoogleAuthProvider();

// Expose to window for other scripts
window.db = db;
window.auth = auth;
window.provider = googleProvider;
window.signInWithGoogle = () => signInWithPopup(auth, googleProvider);
window.signInAnonymously = () => signInAnonymously(auth);
window.signOutUser = () => signOut(auth);

// Theme Logic
function applyTheme(theme) {
    if (theme === 'light') {
        document.documentElement.classList.add('theme-light');
        document.documentElement.classList.remove('theme-dark');
    } else {
        document.documentElement.classList.add('theme-dark');
        document.documentElement.classList.remove('theme-light');
    }
    localStorage.setItem('theme', theme);
}

// Init Theme
const savedTheme = localStorage.getItem('theme') || 'dark';
applyTheme(savedTheme);

window.toggleTheme = () => {
    const current = localStorage.getItem('theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    // Update profile if logged in
    if (auth.currentUser) {
        const userProfileRef = doc(db, 'users', auth.currentUser.uid, 'data', 'profile');
        setDoc(userProfileRef, { theme: next }, { merge: true });
    }
};

// Mouse Move Effect
window.addEventListener('mousemove', (e) => {
    const { clientX, clientY } = e;
    const { innerWidth, innerHeight } = window;
    document.documentElement.style.setProperty('--mouse-x', `${(clientX / innerWidth) * 100}%`);
    document.documentElement.style.setProperty('--mouse-y', `${(clientY / innerHeight) * 100}%`);
});

// Auth State Listener
onAuthStateChanged(auth, async (user) => {
    window.currentUser = user;

    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('userChanged', { detail: { user } }));

    // Presence System
    if (user) {
        // We are authenticated
        const uid = user.uid;
        const userStatusDatabaseRef = ref(db_realtime, '/status/' + uid);

        // Reference to the special '.info/connected' path in RTDB
        const isOfflineForDatabase = {
            state: 'offline',
            last_changed: serverTimestamp(),
        };

        const isOnlineForDatabase = {
            state: 'online',
            last_changed: serverTimestamp(),
        };

        const connectedRef = ref(db_realtime, '.info/connected');
        onValue(connectedRef, (snapshot) => {
            if (snapshot.val() == false) {
                return;
            }
            // If we are here, we are connected
            // 1. Set onDisconnect handler to set status to offline when we lose connection
            onDisconnect(userStatusDatabaseRef).set(isOfflineForDatabase).then(() => {
                // 2. Set current status to online
                set(userStatusDatabaseRef, isOnlineForDatabase);
            });
        });
    }

    if (user) {
        // Sync theme from DB
        try {
            const userProfileRef = doc(db, 'users', user.uid, 'data', 'profile');
            const docSnap = await getDoc(userProfileRef);
            if (docSnap.exists() && docSnap.data().theme) {
                applyTheme(docSnap.data().theme);
            }
        } catch (e) {
            console.error("Error fetching profile", e);
        }
    }
});

// Global Online Counter (Available to all pages)
const allUsersStatusRef = ref(db_realtime, 'status');
onValue(allUsersStatusRef, (snapshot) => {
    const data = snapshot.val();
    if (data) {
        // Count keys where state == 'online'
        const count = Object.values(data).filter(u => u.state === 'online').length;
        window.dispatchEvent(new CustomEvent('onlineUsersUpdate', { detail: { count } }));
    }
});

// --- GLOBAL XP SYSTEM ---
import { doc, getDoc, setDoc, updateDoc } from "firebase/firestore";

window.addXP = async (amount, reason) => {
    if (!window.currentUser) return;
    const userRef = doc(window.db, 'users', window.currentUser.uid, 'data', 'profile');

    try {
        const snap = await getDoc(userRef);
        let currentXP = 0;
        if (snap.exists() && snap.data().xp) {
            currentXP = snap.data().xp;
        }
        const newXP = currentXP + amount;
        await setDoc(userRef, { xp: newXP }, { merge: true });

        // Dispatch event for UI updates
        window.dispatchEvent(new CustomEvent('xpAdded', { detail: { amount, reason, total: newXP } }));

        // Optional: Call addNotification if available
        if (window.addNotification) {
            window.addNotification(`+${amount} XP: ${reason}`, 'success');
        }
    } catch (e) {
        console.error("XP Error", e);
    }
};
