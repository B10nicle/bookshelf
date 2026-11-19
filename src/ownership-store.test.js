import { beforeEach, describe, expect, it } from 'vitest';
import { mergedOwnership, OWNED_KEY, readOwned, writeOwned } from './ownership-store';

describe('ownership storage', () => {
  beforeEach(() => localStorage.clear());
  it('persists ISBN ownership locally', () => {
    writeOwned(new Set(['9781', '9782']));
    expect([...readOwned()]).toEqual(['9781', '9782']);
  });
  it('recovers gracefully from invalid stored data and merges remote ownership', () => {
    localStorage.setItem(OWNED_KEY, 'not-json');
    expect(readOwned()).toEqual(new Set());
    expect([...mergedOwnership(new Set(['9781']), new Set(['9782', '9781']))]).toEqual(['9781', '9782']);
  });
});
