# Writeups web

Osobní web na writeupy a poznámky v **dark/terminálovém** stylu. Příspěvky píšeš
jako `.md` soubory ve složce [`posts/`](posts/) — malý generátor v Pythonu z nich
udělá statické HTML stránky a GitHub Actions je samo nasadí na GitHub Pages.

- **Žádné závislosti** — stačí Python 3 (žádný `npm install`, žádný balíček navíc).
- **Předrenderované stránky** — dobré pro Google i náhledy odkazů, funguje i bez JS.
- **Vyhledávání + filtr podle kategorií**, přepínač jazyků **EN/VI**, RSS, sitemap.

---

## Rychlý start (lokální náhled)

```bash
python3 scripts/dev.py
```

Otevři <http://localhost:8000>. Uprav cokoliv v `posts/`, `src/` nebo `assets/`
a stránka se sama obnoví. (Jen sestavit do `dist/` bez serveru: `python3 scripts/build.py`.)

## Přidání příspěvku

Vytvoř soubor v `posts/`, třeba `posts/muj-box.md`. Název souboru = adresa
(`/writeups/muj-box/`). Nahoru dej frontmatter:

```markdown
---
title: Můj první box
date: 2026-10-11
category: Web
summary: Jedna dvě věty na kartu a do náhledu odkazu.
featured: false
tags: [sqli, recon]
---

## Tady začíná obsah
Zbytek píšeš v Markdownu.
```

Pole: `title`, `date` (`RRRR-MM-DD`), `category`, `summary` (když chybí, vezme se
první odstavec), `featured` (`true` = na úvodní stránku), `tags`, `draft`
(`true` = zatím nezveřejnit). Víc i s ukázkou formátování je v příspěvku
**„Welcome — start here“** přímo na webu.

## Dvojjazyčný příspěvek (EN/VI)

Ke každému příspěvku můžeš přidat překlad jako `posts/<slug>.<jazyk>.md`:

```
posts/edon.md        # výchozí jazyk (EN)
posts/edon.vi.md     # vietnamská verze téhož příspěvku
```

Přepínač EN/VI v hlavičce pak přepne i **tělo článku, titulek a perex** (ne jen
rozhraní). Když překlad chybí, zobrazí se výchozí jazyk. Metadata (`date`,
`category`, `featured`) se berou z výchozího souboru; v `.vi.md` stačí `title`,
`summary` a obsah.

## Úprava webu

Vše osobní je v jednom souboru: [`src/config.py`](src/config.py) — jméno, handle,
odkazy, kategorie (a jejich barvy), certifikace a texty sekcí O mně / Certifikace.
Přepínač EN/VI překládá rozhraní a tyhle texty; **těla příspěvků zůstávají tak,
jak je napíšeš**.

## Nasazení na GitHub Pages

1. Nahraj repozitář na GitHub (branch `main`).
2. **Settings → Pages → Build and deployment → Source: `GitHub Actions`.**
3. Pushni na `main`. Workflow [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)
   web sestaví a nasadí. Od té doby stačí přidat `.md` a pushnout.

Adresu webu i podcestu (`/nazev-repa/`) workflow dopočítá sám podle názvu
repozitáře — nic nenastavuješ. Výjimka: **vlastní doména** — pak v `src/config.py`
nastav `base = "/"` a `siteUrl = "https://tvoje-domena"` a přidej soubor
`static/CNAME` s doménou.

## Struktura

```
posts/        # tvoje příspěvky (.md) — tohle je to, co budeš měnit nejčastěji
src/
  config.py   # konfigurace webu (jméno, odkazy, kategorie, texty, i18n)
  mdrender.py # Markdown -> HTML (bez závislostí)
  templates.py# HTML šablony stránek
assets/       # style.css + app.js (kopírují se do webu)
static/       # soubory nasazené 1:1 do kořene (favicon, obrázky, CNAME, CV…)
scripts/      # build.py (generátor), dev.py (náhled), serve.py (server)
dist/         # VÝSTUP generátoru — negituje se, přepisuje se buildem
```

## Jak to funguje

`scripts/build.py` přečte `posts/*.md`, vyrenderuje je a vytvoří do `dist/`:
úvodní stránku, seznam writeupů, stránku pro každý příspěvek, O mně, Certifikace,
`posts.json`, `feed.xml`, `sitemap.xml`, `robots.txt` a `404.html`. Složka `dist/`
je čistě generovaná — neupravuj ji ručně.

Podporovaný Markdown: nadpisy `#`–`###` (s kotvami), `**tučně**`, `*kurzíva*`,
`` `kód` ``, odkazy, odrážkové i číslované seznamy, `> citace`, `---` čára a
```` ``` ```` bloky kódu s jazykem (s tlačítkem na zkopírování). HTML v příspěvku
se escapuje, takže se nikdy nespustí.
