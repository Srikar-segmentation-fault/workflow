import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import LanguageSwitcher from '../components/LanguageSwitcher';
import client from '../api/client';
import styles from './LoginPage.module.css';

// MOCK: remove this block and use the real API call below when backend is ready
const MOCK_USERS = [
  { id: '1', name: 'Alice Manager', email: 'manager@demo.com', role: 'manager', password: 'password' },
  { id: '2', name: 'Bob Employee', email: 'employee@demo.com', role: 'employee', password: 'password' },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // ── MOCK LOGIN ──────────────────────────────────────────────────────────
      // TODO: replace this block with the real API call below when backend is ready
      await new Promise((r) => setTimeout(r, 400)); // simulate network delay
      const found = MOCK_USERS.find(
        (u) => u.email === email && u.password === password
      );
      if (!found) throw new Error(t('auth.invalidCredentials'));
      const { password: _pw, ...userData } = found;
      const mockToken = `mock-jwt-${userData.role}-${Date.now()}`;
      login(mockToken, userData);
      // ── END MOCK ────────────────────────────────────────────────────────────

      // ── REAL API CALL (uncomment when backend is ready) ─────────────────────
      // const { data } = await client.post('/api/auth/login', { email, password });
      // login(data.token, data.user);
      // ── END REAL API ────────────────────────────────────────────────────────

      navigate(userData.role === 'manager' ? '/manager' : '/employee');
    } catch (err) {
      setError(err.message || t('auth.loginFailed'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        {/* Language switcher at top of login card */}
        <div className={styles.langRow}>
          <LanguageSwitcher />
        </div>

        <div className={styles.logo}>
          <span className={styles.logoIcon}>⚡</span>
          <h1 className={styles.logoText}>{t('app.name')}</h1>
        </div>
        <p className={styles.tagline}>{t('app.tagline')}</p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="email">{t('auth.email')}</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('auth.emailPlaceholder')}
              required
              autoFocus
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="password">{t('auth.password')}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('auth.passwordPlaceholder')}
              required
            />
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" className={styles.btn} disabled={loading}>
            {loading ? t('auth.signingIn') : t('auth.signIn')}
          </button>
        </form>

        <p className={styles.hint}>
          {t('auth.demoHint')} &nbsp;<code>password</code>
        </p>
      </div>
    </div>
  );
}
