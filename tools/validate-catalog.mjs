import { readFileSync } from 'node:fs';
import { z } from 'zod';

const topicCodes = new Set(['java', 'spring', 'kotlin', 'scala', 'jvm', 'architecture', 'algorithms', 'ddd', 'hibernate', 'compilers', 'kafka', 'misc', 'dsl', 'android', 'related', 'tools']);
const bookSchema = z.object({
  id: z.string().regex(/^(\d{10}|\d{13}|\d{9}X)$/),
  isbn: z.string().min(10),
  title: z.string().min(2),
  workId: z.string().min(3),
  workTitle: z.string().min(2),
  authors: z.array(z.string().min(2)).min(1),
  publisher: z.string().min(2),
  year: z.string().regex(/^\d{4}$/),
  edition: z.string(),
  topics: z.array(z.string()).min(1),
  coverUrl: z.string().url().refine((url) => url.startsWith('https://ik.imagekit.io/bookshelf/'), 'coverUrl must use the ImageKit bookshelf CDN'),
  sourceUrl: z.string().url().refine((url) => url.startsWith('https://'), 'sourceUrl must use HTTPS'),
}).strict();
const catalogSchema = z.object({ researchedAt: z.string().regex(/^\d{4}-\d{2}-\d{2}$/), books: z.array(bookSchema).min(1) }).strict();

const catalog = catalogSchema.parse(JSON.parse(readFileSync(new URL('../src/catalog-data.json', import.meta.url), 'utf8')));
const ids = new Set();
for (const book of catalog.books) {
  if (ids.has(book.id)) throw new Error(`Duplicate ISBN in catalog data: ${book.id}`);
  ids.add(book.id);
  for (const topic of book.topics) if (!topicCodes.has(topic)) throw new Error(`Unknown topic "${topic}" for ${book.id}`);
}
console.log(`Catalog validation passed: ${catalog.books.length} editions, ${ids.size} unique ISBNs.`);
