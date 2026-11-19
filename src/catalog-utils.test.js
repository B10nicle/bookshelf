import { describe, expect, it } from 'vitest';
import { catalogGroups } from './catalog-utils';

const books = [
  { id: 'one', workId: 'java', workTitle: 'Java', title: 'Java 17', publisher: 'Питер', isbn: '1', year: '2022', edition: '', authors: ['А'], topics: ['java'] },
  { id: 'two', workId: 'java', workTitle: 'Java', title: 'Java 21', publisher: 'Питер', isbn: '2', year: '2024', edition: '', authors: ['А'], topics: ['java', 'jvm'] },
  { id: 'three', workId: 'kafka', workTitle: 'Kafka', title: 'Kafka в действии', publisher: 'ДМК Пресс', isbn: '3', year: '2023', edition: '', authors: ['Б'], topics: ['kafka'] },
];

describe('catalogGroups', () => {
  it('intersects search, publisher and topic filters', () => {
    const result = catalogGroups(books, { query: '21', publisher: 'Питер', topic: 'java' });
    expect(result).toHaveLength(1);
    expect(result[0].books.map((book) => book.id)).toEqual(['two']);
  });

  it('keeps only owned editions and moves owned groups last in regular view', () => {
    expect(catalogGroups(books, { onlyOwned: true, owned: new Set(['two']) })[0].books.map((book) => book.id)).toEqual(['two']);
    expect(catalogGroups(books, { owned: new Set(['three']) }).at(-1).id).toBe('kafka');
  });

  it('sorts groups by year, title or publisher', () => {
    expect(catalogGroups(books, { sort: 'year' }).map((group) => group.id)).toEqual(['java', 'kafka']);
    expect(catalogGroups(books, { sort: 'title' }).map((group) => group.id)).toEqual(['java', 'kafka']);
    expect(catalogGroups(books, { sort: 'publisher' }).map((group) => group.id)).toEqual(['kafka', 'java']);
  });
});
