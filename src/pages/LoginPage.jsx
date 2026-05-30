import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { MOCK_USERS } from '../api/mockData';
import styles from './LoginPage.module.css';

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
      await new Promise((r) => setTimeout(r, 300));
      const found = MOCK_USERS.find(
        (u) => u.email === email && u.password === password
      );
      if (!found) throw new Error(t('auth.invalidCredentials'));
      const { password: _pw, ...userData } = found;
      login(`mock-jwt-${userData.role}-${Date.now()}`, userData);
      navigate(userData.role === 'manager' ? '/manager' : '/employee');
    } catch (err) {
      setError(err.message || t('auth.loginFailed'));
    } finally {
      setLoading(false);
    }
  }

  const employees = MOCK_USERS.filter((u) => u.role === 'employee');

  return (
    <div className={styles.page}>
      <div className={styles.card}>
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

        {/* Quick-fill demo accounts */}
        <div className={styles.demoAccounts}>
          <p className={styles.demoTitle}>Demo accounts — password: <code>password</code></p>
          <div className={styles.demoGrid}>
            <button
              type="button"
              className={`${styles.demoBtn} ${styles.demoBtnManager}`}
              onClick={() => { setEmail('manager@demo.com'); setPassword('password'); }}
            >
              👔 Alice Manager
            </button>
            {employees.map((emp) => (
              <button
                key={emp.id}
                type="button"
                className={styles.demoBtn}
                onClick={() => { setEmail(emp.email); setPassword('password'); }}
              >
                👤 {emp.name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
