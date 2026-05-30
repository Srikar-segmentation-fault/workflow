import { useTranslation } from 'react-i18next';
import styles from './LanguageSwitcher.module.css';

const LANGUAGES = [
  { code: 'en', label: 'EN', nativeName: 'English' },
  { code: 'te', label: 'తె', nativeName: 'తెలుగు' },
  { code: 'hi', label: 'हि', nativeName: 'हिन्दी' },
];

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const current = i18n.language?.split('-')[0] || 'en';

  function handleChange(e) {
    i18n.changeLanguage(e.target.value);
  }

  return (
    <div className={styles.wrapper} title="Change language">
      <span className={styles.globe}>🌐</span>
      <select
        className={styles.select}
        value={current}
        onChange={handleChange}
        aria-label="Select language"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.label} — {lang.nativeName}
          </option>
        ))}
      </select>
    </div>
  );
}
