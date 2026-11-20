import { useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import catalog from './catalog-data.json';
import { BookGroup } from './components/BookGroup';
import { AuthDialog } from './components/AuthDialog';
import { catalogGroups, TOPICS } from './catalog-utils';
import { firebaseAuth } from './firebaseClient';
import { useOwnership } from './hooks/useOwnership';
import './styles.css';
import './sync.css';
import './ux.css';

function App() {
  const [query, setQuery] = useState('');
  const [publisher, setPublisher] = useState('');
  const [topic, setTopic] = useState('');
  const [onlyOwned, setOnlyOwned] = useState(false);
  const [sort, setSort] = useState('recommended');
  const [showFilters, setShowFilters] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const accountButton = useRef(null);
  const { owned, user, syncState, syncError, toggleOwnership } = useOwnership();
  const closeAuth = () => {
    setShowAuth(false);
    requestAnimationFrame(() => accountButton.current?.focus());
  };
  const publishers = useMemo(() => [...new Set(catalog.books.map((book) => book.publisher))].sort((a, b) => a.localeCompare(b, 'ru')), []);
  const groups = useMemo(() => catalogGroups(catalog.books, { query, publisher, topic, onlyOwned, owned, sort }), [query, publisher, topic, onlyOwned, owned, sort]);
  const ownedCount = catalog.books.filter((book) => owned.has(book.id)).length;
  const syncMessage = syncState === 'synced' ? 'Личная библиотека синхронизирована с Firebase.'
    : syncState === 'syncing' ? 'Синхронизируем личную библиотеку…'
      : syncState === 'error' ? syncError
        : 'Отметки сохраняются в этом браузере. Войдите, чтобы синхронизировать их между устройствами.';
  const activeFilters = [
    query && `Поиск: ${query}`,
    publisher && `Издательство: ${publisher}`,
    topic && `Тема: ${TOPICS.find(([id]) => id === topic)?.[1]}`,
    onlyOwned && 'Мои книги',
  ].filter(Boolean);
  const resetFilters = () => { setQuery(''); setPublisher(''); setTopic(''); setOnlyOwned(false); };

  return <main id="top" className="catalog">
    <header className="heading">
      <div className="brand"><span className="brand-mark" aria-hidden="true">▦</span><div><h1>Книжный шкаф</h1><p className="brand-subtitle">Ваша личная полка</p></div></div>
      <div className="account"><span className={user ? `account-email ${syncState}` : 'account-email'}>{user ? user.email : 'Гостевой режим'}</span><button ref={accountButton} onClick={() => setShowAuth(true)}>{user ? 'Аккаунт' : 'Войти'}</button></div>
    </header>
    <section className="hero" aria-label="Личная библиотека">
      <div><h2 className="hero-title">Соберите коллекцию</h2><p className="hero-count">{catalog.books.length} книг в коллекции</p></div>
      <button className={`library-summary ${onlyOwned ? 'active' : ''}`} aria-pressed={onlyOwned} onClick={() => setOnlyOwned(!onlyOwned)}><span className="library-label">В моей библиотеке</span><span className="library-count"><strong>{ownedCount}</strong><small>{ownedCount === 1 ? 'книга' : ownedCount > 1 && ownedCount < 5 ? 'книги' : 'книг'}</small></span></button>
    </section>
    <section className="catalog-controls" aria-label="Поиск и фильтры">
      <div className="search-row"><input value={query} onChange={(event) => setQuery(event.target.value)} type="search" placeholder="Название, автор или ISBN" aria-label="Поиск" /><button className={showFilters ? 'filter-toggle active' : 'filter-toggle'} type="button" aria-expanded={showFilters} aria-controls="advanced-filters" onClick={() => setShowFilters(!showFilters)}>Фильтры{activeFilters.length ? ` · ${activeFilters.length}` : ''}</button></div>
      <div className="topic-area"><p className="control-label">Выберите тему</p><div className="topic-buttons" role="group" aria-label="Быстрый выбор тематики">{TOPICS.map(([id, label]) => <button key={id} className={topic === id ? 'active' : ''} aria-pressed={topic === id} onClick={() => setTopic(id)}>{label}</button>)}</div></div>
      {showFilters && <div id="advanced-filters" className="advanced-filters"><label>Издательство<select value={publisher} onChange={(event) => setPublisher(event.target.value)}><option value="">Все издательства</option>{publishers.map((name) => <option key={name}>{name}</option>)}</select></label><label>Порядок книг<select value={sort} onChange={(event) => setSort(event.target.value)}><option value="recommended">По подборке</option><option value="year">Сначала новые</option><option value="title">По названию</option><option value="publisher">По издательству</option></select></label></div>}
    </section>
    {activeFilters.length > 0 && <div className="active-filters" aria-label="Активные фильтры"><span>{activeFilters.join(' · ')}</span><button type="button" onClick={resetFilters}>Сбросить фильтры</button></div>}
    {user && <p className={`sync-note ${syncState}`} role="status">{syncMessage}</p>}
    <div className="grid">{groups.map((group) => <BookGroup key={group.id} group={group} owned={owned} onToggle={toggleOwnership} />)}</div>
    {!groups.length && <p className="empty">По этому запросу ничего не найдено.</p>}
    <footer><a className="back-to-top" href="#top"><span>↑</span>Наверх</a></footer>
    {showAuth && <AuthDialog user={user} onClose={closeAuth} onLogin={firebaseAuth.signIn} onRegister={firebaseAuth.register} onLogout={firebaseAuth.signOut} />}
  </main>;
}

createRoot(document.getElementById('root')).render(<App />);
