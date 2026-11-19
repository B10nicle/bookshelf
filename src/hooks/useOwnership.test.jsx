import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { OWNED_KEY } from '../ownership-store';

const mocks = vi.hoisted(() => ({
  subscribe: vi.fn(),
  getRemoteOwnership: vi.fn(),
  saveRemoteOwnership: vi.fn(),
  removeRemoteOwnership: vi.fn(),
}));

vi.mock('../firebaseClient', () => ({
  firebaseAuth: { subscribe: mocks.subscribe },
  getRemoteOwnership: mocks.getRemoteOwnership,
  saveRemoteOwnership: mocks.saveRemoteOwnership,
  removeRemoteOwnership: mocks.removeRemoteOwnership,
}));

import { useOwnership } from './useOwnership';

describe('useOwnership', () => {
  beforeEach(() => {
    localStorage.clear(); vi.clearAllMocks();
    mocks.saveRemoteOwnership.mockResolvedValue();
    mocks.removeRemoteOwnership.mockResolvedValue();
  });

  it('merges guest and remote ownership after sign in', async () => {
    localStorage.setItem(OWNED_KEY, JSON.stringify(['local-book']));
    mocks.getRemoteOwnership.mockResolvedValue(new Set(['remote-book']));
    mocks.subscribe.mockImplementation((listener) => { listener({ uid: 'reader' }); return vi.fn(); });
    const { result } = renderHook(() => useOwnership());
    await waitFor(() => expect(result.current.syncState).toBe('synced'));
    expect([...result.current.owned]).toEqual(expect.arrayContaining(['local-book', 'remote-book']));
    expect(mocks.saveRemoteOwnership).toHaveBeenCalledWith('reader', 'local-book');
  });

  it('keeps a local change and reports a sync error when Firestore fails', async () => {
    mocks.subscribe.mockImplementation((listener) => { listener({ uid: 'reader' }); return vi.fn(); });
    mocks.getRemoteOwnership.mockResolvedValue(new Set());
    mocks.saveRemoteOwnership.mockRejectedValue(new Error('offline'));
    const { result } = renderHook(() => useOwnership());
    await waitFor(() => expect(result.current.syncState).toBe('synced'));
    await act(() => result.current.toggleOwnership('book'));
    expect(result.current.owned.has('book')).toBe(true);
    expect(result.current.syncState).toBe('error');
  });
});
