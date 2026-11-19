import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AuthDialog } from './AuthDialog';

describe('AuthDialog', () => {
  it('submits login with Enter and closes with Escape', async () => {
    const onLogin = vi.fn().mockResolvedValue();
    const onClose = vi.fn();
    render(<AuthDialog onClose={onClose} onLogin={onLogin} onRegister={vi.fn()} onLogout={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'reader@example.com' } });
    fireEvent.change(screen.getByLabelText('Пароль'), { target: { value: 'a-secure-password' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Войти' }).closest('form'));
    expect(onLogin).toHaveBeenCalledWith('reader@example.com', 'a-secure-password');
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });
});
