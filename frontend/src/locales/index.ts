import { createI18n } from "vue-i18n";

// Import locale messages
import en from "./en.json";
import de from "./de.json";
import es from "./es.json";

// ============================================================

const messages = {
  en,
  de,
  es
};

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem("language") || "en",
  fallbackLocale: "en",
  messages
});

export default i18n;
