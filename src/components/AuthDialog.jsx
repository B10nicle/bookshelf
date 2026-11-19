import { useEffect, useRef, useState } from 'react';

const focusable = 'button:not([disabled]), input:not([disabled])';

export function AuthDialog({ user, onClose, onLogin, onRegister, onLogout }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const dialogRef = useRef(null);
  const emailRef = useRef(null);

  useEffect(() => { (user ? dialogRef.current?.querySelector('.close') : emailRef.current)?.focus(); }, [user]);
  const submit = async (mode) => {
    setBusy(true); setError('');
    try {
      if (mode === 'login') await onLogin(email.trim(), password);
      else await onRegister(email.trim(), password);
      onClose();
    } catch (reason) {
      const message = reason?.code === 'auth/invalid-credential' ? 'Проверьте email и пароль.'
        : reason?.code === 'auth/email-already-in-use' ? 'Этот email уже зарегистрирован. Войдите в аккаунт.'
        : reason?.code === 'auth/weak-password' ? 'Пароль должен быть не короче 12 символов.'
        : 'Не удалось выполнить действие. Попробуйте ещё раз.';
      setError(message);
    } finally { setBusy(false); }
  };
  const onKeyDown = (event) => {
    if (event.key === 'Escape') { event.preventDefault(); onClose(); return; }
    if (event.key !== 'Tab') return;
    const elements = [...dialogRef.current.querySelectorAll(focusable)];
    const first = elements[0], last = elements.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  };

  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section ref={dialogRef} className="auth-dialog" role="dialog" aria-modal="true" aria-labelledby="auth-title" onKeyDown={onKeyDown}>
      <button className="close" type="button" onClick={onClose} aria-label="Закрыть">×</button>
      <h2 id="auth-title">{user ? 'Аккаунт' : 'Личная библиотека'}</h2>
      {user ? <>
        <p className="auth-copy">Ваши отметки «У меня есть» синхронизируются между устройствами.</p>
        <div className="signed-in"><span className="sync-dot" />{user.email}</div>
        <button className="logout" type="button" onClick={() => onLogout().then(onClose)}>Выйти из аккаунта</button>
      </> : <form onSubmit={(event) => { event.preventDefault(); submit('login'); }}>
        <p className="auth-copy">Сохраняйте отметки «У меня есть» и открывайте их на любом устройстве.</p>
        <label>Email<input ref={emailRef} value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" placeholder="you@example.com" required /></label>
        <label>Пароль<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" minLength="12" placeholder="Не менее 12 символов" required /></label>
        <p className="form-hint">Если аккаунта ещё нет, регистрация займёт один шаг.</p>
        {error && <p className="form-error" role="status">{error}</p>}
        <div className="auth-actions">
          <button className="primary" type="submit" disabled={busy}>Войти</button>
          <button className="secondary" type="button" disabled={busy} onClick={() => submit('register')}>Создать аккаунт</button>
        </div>
      </form>}
    </section>
  </div>;
}
