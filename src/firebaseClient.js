import { initializeApp } from 'firebase/app';
import { getAuth, onAuthStateChanged, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { collection, deleteDoc, doc, getDocs, getFirestore, serverTimestamp, setDoc } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: 'AIzaSyC73CklHmDbbFNhuunTJ9afTZWr1mYVhSM',
  authDomain: 'read-in-60-seconds.firebaseapp.com',
  projectId: 'read-in-60-seconds',
  storageBucket: 'read-in-60-seconds.firebasestorage.app',
  messagingSenderId: '157768008666',
  appId: '1:157768008666:web:64bc6c7f87fbe9aa4f36e3',
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

export const firebaseAuth = {
  subscribe: (listener) => onAuthStateChanged(auth, listener),
  signIn: (email, password) => signInWithEmailAndPassword(auth, email, password),
  register: (email, password) => createUserWithEmailAndPassword(auth, email, password),
  signOut: () => signOut(auth),
};

export async function getRemoteOwnership(uid) {
  const snapshot = await getDocs(collection(db, 'users', uid, 'catalogOwnership'));
  return new Set(snapshot.docs.filter((entry) => entry.data().owned).map((entry) => entry.id));
}

export function saveRemoteOwnership(uid, isbn) {
  return setDoc(doc(db, 'users', uid, 'catalogOwnership', isbn), {
    owned: true,
    updatedAt: serverTimestamp(),
  }, { merge: true });
}

export function removeRemoteOwnership(uid, isbn) {
  return deleteDoc(doc(db, 'users', uid, 'catalogOwnership', isbn));
}
