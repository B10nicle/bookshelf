import { useEffect, useRef, useState } from 'react';
import { firebaseAuth, getRemoteOwnership, removeRemoteOwnership, saveRemoteOwnership } from '../firebaseClient';
import { mergedOwnership, readOwned, writeOwned } from '../ownership-store';

export function useOwnership() {
  const [owned, setOwned] = useState(readOwned);
  const [user, setUser] = useState(null);
  const [syncState, setSyncState] = useState('local');
  const [syncError, setSyncError] = useState('');
  const ownedRef = useRef(owned);
  const replaceOwned = (next) => { ownedRef.current = next; setOwned(next); writeOwned(next); };

  useEffect(() => firebaseAuth.subscribe(async (nextUser) => {
    setUser(nextUser);
    if (!nextUser) { setSyncState('local'); setSyncError(''); return; }
    setSyncState('syncing'); setSyncError('');
    try {
      const remote = await getRemoteOwnership(nextUser.uid);
      const local = ownedRef.current;
      const merged = mergedOwnership(local, remote);
      replaceOwned(merged);
      await Promise.all([...local].filter((isbn) => !remote.has(isbn)).map((isbn) => saveRemoteOwnership(nextUser.uid, isbn)));
      setSyncState('synced');
    } catch {
      setSyncState('error');
      setSyncError('Не удалось синхронизировать библиотеку. Проверьте подключение и повторите попытку.');
    }
  }), []);

  const toggleOwnership = async (isbn) => {
    const next = new Set(ownedRef.current);
    next.has(isbn) ? next.delete(isbn) : next.add(isbn);
    replaceOwned(next);
    if (!user) return;
    setSyncState('syncing'); setSyncError('');
    try {
      next.has(isbn) ? await saveRemoteOwnership(user.uid, isbn) : await removeRemoteOwnership(user.uid, isbn);
      setSyncState('synced');
    } catch {
      setSyncState('error');
      setSyncError('Изменение сохранено на этом устройстве, но пока не синхронизировано.');
    }
  };

  return { owned, user, syncState, syncError, toggleOwnership };
}
