# tdma4 — Tout autour de la terre…

Site statique du tour du monde 2007–2008, généré avec [Astro](https://astro.build).

## Structure

| Dossier | Contenu |
|---|---|
| `src/data/articles.json` | Les 36 récits (texte nettoyé + liste des photos), produits depuis les fichiers Word |
| `src/data/rubriques.json` | Les rubriques (pays), dans l'ordre des fichiers Word |
| `src/data/itinerary.json` | Les 61 étapes de la carte (lieu, date, coordonnées, moyen de transport) |
| `src/data/covers.json`, `hero.json` | Photo de couverture de chaque pays, photos de l'accueil |
| `src/data/families.json` | Liens « D'autres familles autour du monde » |
| `public/photos/<pays>/` | Photos (une par fichier, optimisées) |
| `public/films/` | Films MP4 (nom = repère « Insérer film … » des fichiers Word) |
| `functions/api/contact.js` | Formulaire de contact (fonction Cloudflare) |

## Commandes

```bash
npm install
npm run dev      # aperçu local sur http://localhost:4321
npm run build    # génère le site dans dist/
```

Reconvertir les fichiers Word (après correction d'un texte) :

```bash
python3 scripts/convert.py <dossier des .docx> . <dossier temporaire>
```

## Formulaire de contact

Variables à déclarer dans l'hébergeur (jamais dans le code) :

- `CONTACT_TO` : adresse qui reçoit les messages
- `BREVO_API_KEY` : clé API Brevo (envoi des e-mails)
- `TURNSTILE_SECRET` : clé secrète anti-robots Cloudflare Turnstile
- `PUBLIC_TURNSTILE_SITEKEY` : clé publique Turnstile (au moment du build)

## Mise en ligne (Cloudflare Pages)

- Build command : `npm run build` — Build output directory : `dist` — Variable `NODE_VERSION` = `22`
- Domaine : `tdma4.fr` (zone DNS gérée par Cloudflare), `www.tdma4.fr` redirigé vers `tdma4.fr`
