import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import styles from './LogoutButton.module.css';

export default function LogoutButton() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className={styles.wrapper}>
      <span className={styles.name}>{user?.name}</span>
      <button className={styles.btn} onClick={handleLogout}>
        Sign Out
      </button>
    </div>
  );
}
