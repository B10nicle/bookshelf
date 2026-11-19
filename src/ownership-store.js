export const OWNED_KEY = 'read-in-60-seconds.catalog.owned.v1';

export function readOwned() {
  try { return new Set(JSON.parse(localStorage.getItem(OWNED_KEY) || '[]')); } catch { return new Set(); }
}

export function writeOwned(ids) {
  localStorage.setItem(OWNED_KEY, JSON.stringify([...ids]));
}

export function mergedOwnership(...sets) {
  return new Set(sets.flatMap((ids) => [...ids]));
}
