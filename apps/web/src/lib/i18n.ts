import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import bn from "../locales/bn.json";
import en from "../locales/en.json";

const KEY = "hg.lang";
export type Lang = "bn" | "en";

export function storedLang(): Lang {
  return localStorage.getItem(KEY) === "en" ? "en" : "bn"; // Bangla first
}

export function setLang(lang: Lang): void {
  localStorage.setItem(KEY, lang);
  document.documentElement.lang = lang;
  void i18n.changeLanguage(lang);
}

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, bn: { translation: bn } },
  lng: storedLang(),
  fallbackLng: "en",
  interpolation: { escapeValue: false },
  returnNull: false,
});
document.documentElement.lang = storedLang();

/** Factor ids contain ":" (i18next's namespace separator), so keys use "_" instead. */
export const factorKey = (factor: string): string => `factor.${factor.replace(":", "_")}`;

export default i18n;
