export const TOPICS = [
  ['', 'Все книги'], ['java', 'Java'], ['spring', 'Spring'], ['kotlin', 'Kotlin'], ['scala', 'Scala'], ['jvm', 'JVM'], ['architecture', 'Архитектура'], ['algorithms', 'Алгоритмы'], ['ddd', 'DDD'], ['hibernate', 'Hibernate'], ['compilers', 'Компиляторы'], ['kafka', 'Kafka'], ['misc', 'Разное'],
];

export function catalogGroups(books, { query = '', publisher = '', topic = '', onlyOwned = false, owned = new Set(), sort = 'recommended' }) {
  const needle = query.trim().toLocaleLowerCase('ru');
  const groups = new Map();
  for (const book of books) {
    const searchable = [book.title, book.workTitle, book.publisher, book.isbn, book.year, book.edition, ...book.authors, ...book.topics].join(' ').toLocaleLowerCase('ru');
    if ((needle && !searchable.includes(needle)) || (publisher && book.publisher !== publisher) || (topic && !book.topics.includes(topic)) || (onlyOwned && !owned.has(book.id))) continue;
    if (!groups.has(book.workId)) groups.set(book.workId, { id: book.workId, books: [] });
    groups.get(book.workId).books.push(book);
  }
  const prepared = [...groups.values()]
    .map((group) => ({ ...group, books: [...group.books].sort((a, b) => `${b.year}${b.id}`.localeCompare(`${a.year}${a.id}`)) }));
  return prepared.sort((a, b) => {
    if (sort === 'year') return Number(b.books[0].year) - Number(a.books[0].year) || a.books[0].title.localeCompare(b.books[0].title, 'ru');
    if (sort === 'title') return a.books[0].workTitle.localeCompare(b.books[0].workTitle, 'ru');
    if (sort === 'publisher') return a.books[0].publisher.localeCompare(b.books[0].publisher, 'ru') || a.books[0].workTitle.localeCompare(b.books[0].workTitle, 'ru');
    return Number(a.books.some((book) => owned.has(book.id))) - Number(b.books.some((book) => owned.has(book.id)));
  });
}
