import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import LanguageSwitcher from './LanguageSwitcher';
import styles from './LogoutButton.module.css';

export default function LogoutButton() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className={styles.wrapper}>
      <LanguageSwitcher />
      <span className={styles.name}>{user?.name}</span>
      <button className={styles.btn} onClick={handleLogout}>
        {t('nav.signOut')}
      </button>
    </div>
  );
}
