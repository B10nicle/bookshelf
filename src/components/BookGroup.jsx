function Edition({ book, owned, onToggle }) {
  return <article className="edition">
    <img src={book.coverUrl} alt={`Обложка: ${book.title}`} loading="lazy" />
    <div className="edition-copy">
      <p className="eyebrow">{book.publisher} · {book.year}</p>
      <h3>{book.title}</h3>
      <p className="authors">{book.authors.join(', ')}</p>
      {book.edition && <p className="meta">{book.edition}</p>}
      <p className="meta">ISBN {book.isbn}</p>
      <label className="ownership"><input type="checkbox" checked={owned.has(book.id)} onChange={() => onToggle(book.id)} />У меня есть</label>
      <a href={book.sourceUrl} target="_blank" rel="noreferrer">Страница издания</a>
    </div>
  </article>;
}

export function BookGroup({ group, owned, onToggle }) {
  const book = group.books[0];
  const years = [...new Set(group.books.map((item) => item.year))].sort();
  const range = years.length === 1 ? years[0] : `${years[0]}–${years.at(-1)}`;
  const hasOwned = group.books.some((item) => owned.has(item.id));
  return <section className="book-group">
    <img className="group-cover" src={book.coverUrl} alt={`Обложка: ${book.title}`} loading="lazy" />
    <h2>{book.workTitle}</h2>
    <p className="group-meta">{group.books.length} изд. · {range}</p>
    {hasOwned && <p className="in-library">Есть в библиотеке</p>}
    {group.books.length === 1 ? <label className="ownership"><input type="checkbox" checked={owned.has(book.id)} onChange={() => onToggle(book.id)} />У меня есть</label> : <p className="subtle">Отметьте своё издание ниже.</p>}
    <details>
      <summary>Издания и сведения · {group.books.length}</summary>
      <div className="editions">{group.books.map((item) => <Edition key={item.id} book={item} owned={owned} onToggle={onToggle} />)}</div>
    </details>
  </section>;
}
