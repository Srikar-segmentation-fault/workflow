import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
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
      if (!found) throw new Error('Invalid email or password');
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
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>⚡</span>
          <h1 className={styles.logoText}>WorkFlow</h1>
        </div>
        <p className={styles.tagline}>Task &amp; Accountability Platform</p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              autoFocus
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" className={styles.btn} disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p className={styles.hint}>
          Demo — manager@demo.com / employee@demo.com &nbsp;|&nbsp; password: <code>password</code>
        </p>
      </div>
    </div>
  );
}
