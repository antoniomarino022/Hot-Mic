---
name: telegram-miniapp-ui
description: Costruisce interfacce semplici, pulite e native-feeling per Telegram Mini App (stile Telegram, tipo "In Segreto" / messaggistica anonima) con FastAPI + Jinja2 + htmx + Tailwind. Usa SEMPRE questa skill quando l'utente chiede una UI, un template, una pagina, un componente (lista chat, bolla messaggio, input bar, header, bottom sheet, impostazioni, empty state) per una Mini App Telegram, un'app "tipo Telegram", un client di messaggi/segreti anonimi, o menziona themeParams, WebApp, initData, htmx + Jinja + Tailwind insieme. Applicala anche se l'utente non dice "Telegram" ma chiede "UI pulita senza stile AI" per un'app chat server-rendered. I colori NON sono fissi: si adattano al tema dell'utente in Telegram (chiaro/scuro/custom) tramite le CSS variables del WebApp.
---

# Telegram Mini App UI — FastAPI + Jinja + htmx + Tailwind

Obiettivo: una UI che sembri **parte di Telegram**, non una web app incollata dentro. Semplice, densa il giusto, zero decorazione. Se un elemento non serve a leggere, scrivere o navigare, non c'è.

## Principi (leggi prima di scrivere codice)

1. **I colori vengono da Telegram, mai hardcoded.** Ogni colore è una CSS variable `--tg-theme-*` con fallback. Niente palette propria, niente `blue-500`, niente `gray-100`.
2. **Server-rendered.** Jinja produce HTML, htmx lo scambia. Niente SPA, niente JSON + render client, JS custom minimo (solo bridge Telegram).
3. **Native feel.** Font di sistema, tap target ≥ 44px, stati `active:` al posto di `hover:`, niente scroll orizzontale, safe area rispettate, haptic feedback sulle azioni.
4. **Poche cose, fatte bene.** Una azione primaria per schermata. Usa `MainButton` di Telegram per la CTA principale quando ha senso.

## Anti "AI slop" — VIETATO

- Gradienti, glassmorphism, blur decorativi, glow, ombre grandi (`shadow-lg/xl/2xl`)
- Viola/indigo/"brand color" inventato, qualsiasi colore fuori dal tema
- Card dentro card, bordi + ombra + sfondo insieme, angoli esagerati (`rounded-3xl` su tutto)
- Emoji come icone, hero section, tagline, illustrazioni generiche, badge "New"
- Animazioni di ingresso, hover-scale, bounce, pulse decorativi
- Testo placeholder tipo "Welcome back!", "Let's get started", sottotitoli motivazionali
- Spaziatura gonfia: Telegram è compatto. Righe lista 56–64px, non 100px
- Più di 2 pesi di font per schermata, titoli enormi

Se hai un dubbio: togli. Se è già tolto: va bene così.

## Setup

### Struttura

```
app/
  main.py
  auth.py              # validazione initData
  templates/
    base.html
    chats.html         # pagina intera
    chat.html
    partials/          # SOLO frammenti per htmx
      chat_list.html
      messages.html
      message.html
    macros/
      ui.html          # icon(), avatar(), row()
  static/
    app.css            # output Tailwind
    tg.js              # bridge Telegram (<60 righe)
    htmx.min.js        # self-hosted, versione pinnata
```

### Tailwind (v4, CLI standalone, niente Node)

`static/src.css` → build con `tailwindcss -i static/src.css -o static/app.css --minify`

```css
@import "tailwindcss";

/* 1. Token Telegram con fallback (browser di sviluppo / tema non fornito) */
:root {
  --c-bg:        var(--tg-theme-bg-color, #ffffff);
  --c-secondary: var(--tg-theme-secondary-bg-color, #efeff4);
  --c-section:   var(--tg-theme-section-bg-color, var(--c-bg));
  --c-header:    var(--tg-theme-header-bg-color, var(--c-bg));
  --c-text:      var(--tg-theme-text-color, #000000);
  --c-hint:      var(--tg-theme-hint-color, #8e8e93);
  --c-subtitle:  var(--tg-theme-subtitle-text-color, var(--c-hint));
  --c-link:      var(--tg-theme-link-color, #2481cc);
  --c-accent:    var(--tg-theme-button-color, #2481cc);
  --c-on-accent: var(--tg-theme-button-text-color, #ffffff);
  --c-accent-text: var(--tg-theme-accent-text-color, var(--c-link));
  --c-danger:    var(--tg-theme-destructive-text-color, #e53935);
  --c-sep:       color-mix(in srgb, var(--c-hint) 25%, transparent);
  --c-press:     color-mix(in srgb, var(--c-hint) 14%, transparent);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-tg]) {  /* data-tg viene messo da tg.js quando siamo davvero dentro Telegram */
    --c-bg: #212121; --c-secondary: #0f0f0f; --c-text: #fff; --c-hint: #aaaaaa;
  }
}

/* 2. Esponi i token come utility Tailwind: bg-bg, bg-secondary, text-hint, ... */
@theme inline {
  --color-bg: var(--c-bg);
  --color-secondary: var(--c-secondary);
  --color-section: var(--c-section);
  --color-header: var(--c-header);
  --color-text: var(--c-text);
  --color-hint: var(--c-hint);
  --color-link: var(--c-link);
  --color-accent: var(--c-accent);
  --color-on-accent: var(--c-on-accent);
  --color-accent-text: var(--c-accent-text);
  --color-danger: var(--c-danger);
  --color-sep: var(--c-sep);
  --color-press: var(--c-press);
  --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* 3. Base */
html, body { height: 100%; }
body {
  background: var(--c-secondary); color: var(--c-text);
  font-family: var(--font-sans); font-size: 16px; line-height: 1.35;
  -webkit-font-smoothing: antialiased; -webkit-tap-highlight-color: transparent;
  overscroll-behavior: none;
  padding-top: var(--tg-content-safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
button, a { touch-action: manipulation; }
```

Mai `bg-white`, `text-black`, `border-gray-*`, `text-blue-*`: usa solo i token sopra.

### base.html

```html
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
  <script src="https://telegram.org/js/telegram-web-app.js"></script> {# deve stare nell'head, sincrono #}
  <link rel="stylesheet" href="{{ url_for('static', path='app.css') }}">
  <title>{% block title %}{% endblock %}</title>
</head>
<body hx-boost="true" hx-target="#app" hx-swap="innerHTML" hx-push-url="false">
  <main id="app" class="min-h-dvh">{% block content %}{% endblock %}</main>
  <script src="{{ url_for('static', path='htmx.min.js') }}"></script>
  <script src="{{ url_for('static', path='tg.js') }}"></script>
</body>
</html>
```

### tg.js (bridge, tienilo piccolo)

```js
const tg = window.Telegram?.WebApp;
if (tg) {
  document.documentElement.dataset.tg = "";
  tg.ready();
  tg.expand();
  tg.setHeaderColor?.("secondary_bg_color");
  tg.setBackgroundColor?.("secondary_bg_color");

  // initData in OGNI richiesta htmx → il server valida l'utente
  document.body.addEventListener("htmx:configRequest", (e) => {
    e.detail.headers["X-Telegram-Init-Data"] = tg.initData;
  });

  // BackButton nativo al posto di un "←" disegnato, se la pagina lo richiede
  const sync = () => {
    const back = document.querySelector("[data-back]")?.dataset.back;
    if (back) { tg.BackButton.show(); tg.BackButton.onClick(() => history.back()); }
    else tg.BackButton.hide();
  };
  document.body.addEventListener("htmx:afterSettle", sync); sync();

  // Haptic leggero su tap di elementi marcati
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-haptic]")) tg.HapticFeedback?.impactOccurred("light");
  });
}
```

Per le CTA principali preferisci `tg.MainButton` (testo + `onClick`) a un bottone HTML grande in fondo.

## Auth: validazione initData (FastAPI)

Mai fidarsi di un user id mandato dal client. Valida `initData` ad ogni richiesta con una dependency.

```python
# auth.py
import hmac, hashlib, json, time
from urllib.parse import parse_qsl
from fastapi import Header, HTTPException

BOT_TOKEN = ...  # da env
MAX_AGE = 3600

def get_user(x_telegram_init_data: str = Header("")):
    data = dict(parse_qsl(x_telegram_init_data, keep_blank_values=True))
    received = data.pop("hash", None)
    if not received:
        raise HTTPException(401)
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise HTTPException(401)
    if time.time() - int(data.get("auth_date", 0)) > MAX_AGE:
        raise HTTPException(401)
    return json.loads(data["user"])
```

Nota: la prima pagina (GET iniziale) non ha l'header. Servi una shell minima che fa subito una richiesta htmx (`hx-get="/chats" hx-trigger="load"`) già con l'header, oppure passa `initData` una volta e crea una sessione cookie firmata. Per un'app anonima: mostra alias, non nome/username reali, e non loggare mai `initData`.

## Pattern FastAPI + Jinja + htmx

- **Un template, due modalità.** Stessa route: se `HX-Request` → restituisci solo il frammento, altrimenti pagina intera.

```python
def render(request, page, partial, **ctx):
    tpl = partial if request.headers.get("HX-Request") else page
    return templates.TemplateResponse(request, tpl, ctx)
```

- **Invio messaggio:** `hx-post` sul form, `hx-target="#messages"`, `hx-swap="beforeend"`, il server risponde con la sola bolla. `hx-on::after-request="this.reset()"` per svuotare l'input.
- **Nuovi messaggi:** polling leggero `hx-get="/chat/{id}/new?after={last_id}" hx-trigger="every 3s" hx-swap="beforeend"` oppure SSE (`hx-ext="sse"`) se serve realtime. Parti dal polling.
- **Scroll in fondo** dopo lo swap: `hx-on::after-swap="this.scrollTop = this.scrollHeight"` sul contenitore messaggi.
- **Indicatore di caricamento:** nessuno spinner decorativo. Usa `htmx-request` per abbassare l'opacità del bottone (`.htmx-request { opacity:.6 }`).
- **Errori:** frammento di una riga con `text-danger text-sm`, mai modali di errore.
- **Eliminazioni:** `hx-delete` + `hx-confirm` solo se irreversibile; altrimenti azione immediata con undo.
- Pinna la versione di htmx e self-hostala. Niente `hx-boost` su link esterni.

## Componenti

### Icone
Un solo macro Jinja con SVG inline, stroke `1.75`, `currentColor`, 24px (Lucide-style). Mai emoji, mai icon font.

```jinja
{% macro icon(name, cls="size-6") %}
<svg class="{{ cls }}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  {% if name == "send" %}<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>
  {% elif name == "search" %}<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>
  {% elif name == "plus" %}<path d="M12 5v14M5 12h14"/>
  {% elif name == "lock" %}<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>
  {% endif %}
</svg>
{% endmacro %}
```

### Avatar
Cerchio 48px, iniziale (o simbolo per anonimo) in `text-on-accent`. Tinta derivata dall'hash dell'id **ma sempre dal tema**: `color-mix(in srgb, var(--c-accent) X%, var(--c-text))` variando X, non hue casuali che fuggono dal tema.

### Riga lista chat (il componente più importante)

```html
<a href="/chat/{{ c.id }}" data-haptic
   class="flex items-center gap-3 px-4 py-2.5 bg-bg active:bg-press">
  {{ avatar(c) }}
  <div class="min-w-0 flex-1 border-b border-sep pb-2.5 -mb-2.5">
    <div class="flex items-baseline justify-between gap-2">
      <span class="truncate font-medium">{{ c.title }}</span>
      <span class="shrink-0 text-xs text-hint">{{ c.time }}</span>
    </div>
    <div class="flex items-center justify-between gap-2">
      <span class="truncate text-[15px] text-hint">{{ c.preview }}</span>
      {% if c.unread %}<span class="min-w-5 rounded-full bg-accent px-1.5 text-center text-xs font-medium leading-5 text-on-accent">{{ c.unread }}</span>{% endif %}
    </div>
  </div>
</a>
```
Il separatore parte dopo l'avatar (come Telegram), niente card, niente ombre.

### Header
Sticky, `bg-header`, altezza 48–52px, titolo centrato o a sinistra `font-medium`, sottotitolo `text-xs text-hint`. Niente back arrow disegnata se usi `BackButton` nativo. Border-bottom `border-sep` 1px.

### Bolle messaggio
Sfondo pagina chat: `bg-secondary`. Ricevuto: `bg-section text-text`. Inviato: `bg-accent text-on-accent`.

```html
<div class="flex {{ 'justify-end' if m.mine else 'justify-start' }} px-3 py-0.5">
  <div class="max-w-[80%] px-3 py-1.5 text-[16px] break-words whitespace-pre-wrap
              {{ 'bg-accent text-on-accent rounded-2xl rounded-br-md' if m.mine
                 else 'bg-section text-text rounded-2xl rounded-bl-md' }}">
    {{ m.text }}
    <span class="float-right ml-2 mt-1.5 text-[11px] opacity-60">{{ m.time }}</span>
  </div>
</div>
```
Raggruppa messaggi consecutivi dello stesso autore (raggio ridotto sul lato interno, niente nome ripetuto). Separatore data: pillola piccola centrata `text-xs text-hint`, senza sfondo colorato.

### Input bar
Fissa in basso, `bg-bg`, `border-t border-sep`, padding-bottom con `env(safe-area-inset-bottom)`. `<textarea rows="1">` auto-grow (CSS `field-sizing: content; max-height: 8rem`), `rounded-2xl bg-secondary px-3 py-2`, font-size **16px minimo** (sotto, iOS fa zoom). Bottone invia: cerchio 40px `bg-accent text-on-accent`, visibile solo se c'è testo (`:placeholder-shown` / `peer`). Gestisci la tastiera con `--tg-viewport-stable-height`/`100dvh`.

### Sezioni / impostazioni
Stile "sezioni" Telegram: titolo sezione `text-xs uppercase text-hint px-4 pb-1.5`, righe in `bg-section`, separatori `border-sep` con indent. Switch e radio nativi (`accent-color: var(--c-accent)`), niente toggle custom elaborati.

### Bottom sheet
Solo se serve davvero (azioni su un messaggio). `<dialog>` nativo o div fisso, `bg-bg rounded-t-2xl`, maniglia 36×4px `bg-sep`, voci a 52px. Niente backdrop blur: overlay `bg-black/40`.

### Empty state
Una riga di testo `text-hint` centrata + (opzionale) un'azione. Niente illustrazioni.

### Segreti anonimi (se è il caso d'uso)
Mostra alias coerente per conversazione, mai identità reale; icona `lock` piccola vicino al titolo, non banner "100% anonimo". Evita copy rassicurante o marketing: se serve un avviso privacy, una riga `text-xs text-hint`.

## Tipografia e spaziatura

| Uso | Classi |
|---|---|
| Testo base / messaggi | `text-base` (16px) |
| Titolo riga, header | `text-[17px] font-medium` |
| Anteprima, secondario | `text-[15px] text-hint` |
| Meta (ora, contatori) | `text-xs text-hint` |

Due pesi (400/500). Spaziatura su griglia 4px: padding riga `px-4 py-2.5`, gap tra elementi `gap-3`. Raggi: bolle `rounded-2xl`, input `rounded-2xl`, pillole `rounded-full`, il resto **nessun** raggio (le liste sono full-width).

## Tema e dark mode

- Non scrivere mai `dark:`. Il tema arriva da Telegram, le variabili cambiano da sole; ascolta `tg.onEvent("themeChanged", ...)` solo se devi aggiornare header/background color.
- Testa sempre: tema chiaro, scuro e un tema custom con `button_color` molto chiaro/scuro (controlla che `on-accent` resti leggibile: usa sempre la coppia `bg-accent text-on-accent`).
- Contrasto: il testo secondario è `text-hint`, non `opacity-50` su `text`.

## Accessibilità e dettagli

- Tap target ≥ 44×44px, `aria-label` sui bottoni solo-icona, `lang="it"`.
- Focus visibile (`focus-visible:outline-2 outline-accent`), anche se in Telegram si usa poco.
- `prefers-reduced-motion`: le uniche transizioni ammesse sono `background-color` 100ms.
- Safe area: `--tg-content-safe-area-inset-*` + `env(safe-area-inset-*)` per notch e home indicator.
- Disabilita selezione sulle UI di controllo (`select-none`), non sui messaggi.

## Checklist prima di consegnare

- [ ] Nessun colore hardcoded (`grep -E "#[0-9a-fA-F]{3,6}|bg-(white|black|gray|blue|indigo|purple)"` nei template deve essere vuoto, tranne i fallback in `src.css`)
- [ ] Nessun gradiente, blur, ombra grande, emoji-icona, animazione di ingresso
- [ ] Funziona in tema chiaro, scuro e fuori da Telegram (fallback)
- [ ] Ogni route restituisce frammento con `HX-Request` e pagina intera senza
- [ ] `initData` validato server-side ad ogni richiesta, `hmac.compare_digest`, scadenza `auth_date`
- [ ] Input a 16px, safe area ok, nessuno scroll orizzontale
- [ ] CTA principale su `MainButton` o un solo bottone `bg-accent` per schermata
- [ ] Un solo file CSS buildato, htmx self-hosted e pinnato, JS custom < 100 righe

## Come rispondere all'utente

Quando usi questa skill: consegna template Jinja + route FastAPI minime + (se mancano) `src.css`, `tg.js`, `auth.py`. Spiega solo le scelte non ovvie. Se l'utente chiede qualcosa che viola i principi (es. "aggiungi un gradiente carino"), proponi l'alternativa coerente col tema invece di eseguire alla cieca.
