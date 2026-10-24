const tg = window.Telegram?.WebApp;
if (tg) {
  document.documentElement.dataset.tg = "";
  tg.ready();
  tg.expand();
  tg.setHeaderColor?.("secondary_bg_color");
  tg.setBackgroundColor?.("secondary_bg_color");

  // initData in OGNI richiesta htmx → il server valida l'utente
  document.body.addEventListener("htmx:configRequest", (e) => {
    if (tg.initData) {
      e.detail.headers["X-Telegram-Init-Data"] = tg.initData;
    }
  });

  // BackButton nativo al posto di un "←" disegnato, se la pagina lo richiede
  const sync = () => {
    const back = document.querySelector("[data-back]")?.dataset.back;
    if (back) {
      tg.BackButton.show();
      tg.BackButton.onClick(() => {
        if (back === "history") {
          history.back();
        } else {
          window.location.href = back;
        }
      });
    } else {
      tg.BackButton.hide();
    }
  };
  document.body.addEventListener("htmx:afterSettle", sync);
  sync();

  // Haptic leggero su tap di elementi marcati
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-haptic]")) {
      tg.HapticFeedback?.impactOccurred("light");
    }
  });

  // Gestione tema dinamico Telegram
  tg.onEvent?.("themeChanged", () => {
    tg.setHeaderColor?.("secondary_bg_color");
    tg.setBackgroundColor?.("secondary_bg_color");
  });
}
