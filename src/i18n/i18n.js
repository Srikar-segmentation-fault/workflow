import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import te from './locales/te.json';
import hi from './locales/hi.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      te: { translation: te },
      hi: { translation: hi },
    },
    fallbackLng: 'en',
    // LanguageDetector order: localStorage key 'wf_lang', then browser locale
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'wf_lang',
      cacheUserLanguage: true,
    },
    interpolation: {
      escapeValue: false, // React already escapes
    },
  });

export default i18n;
