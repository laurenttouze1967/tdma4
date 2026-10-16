import articlesJson from '../data/articles.json';
import rubriquesJson from '../data/rubriques.json';
import itineraryJson from '../data/itinerary.json';
import coversJson from '../data/covers.json';
import albumJson from '../data/album.json';
import hdJson from '../data/hd.json';
import albumIndex from '../data/album-index.json';
import extraArticles from '../data/extra-articles.json';
import captionsJson from '../data/captions.json';
const captions = captionsJson as Record<string, string>;

export type Photo = { src: string; w: number; h: number; alt: string; full?: string; fw?: number; fh?: number; orig?: string; date?: string | null; caption?: string };
export type BodyPart =
  | { type: 'html'; html: string }
  | { type: 'photos'; items: number[]; caption?: string }
  | { type: 'film'; file: string };
export type Article = {
  slug: string; title: string; rubrique: string; rubriqueName: string; continent: string | null;
  order: number; date: string; dateApprox?: boolean; place: string | null; excerpt: string;
  words: number; readingMinutes: number; photos: Photo[]; body: BodyPart[];
};
export type Rubrique = {
  slug: string; name: string; continent: string | null; num: number; cover: Photo | null;
  articles: string[]; photoCount: number;
};
export type Stop = {
  name: string; country: string; lat: number; lon: number; date: string; until?: string; dateApprox: boolean;
  mode: 'avion' | 'bateau' | 'route' | 'bus' | 'train' | null; transit?: boolean; article: string | null; note: string;
};

// Photos des récits : on remplace par une meilleure définition quand l'album en contient une
type HD = { src: string; w: number; h: number; full: string; fw: number; fh: number };
const hd = hdJson as Record<string, HD>;
const upgrade = (p: Photo): Photo => {
  const h = hd[p.src];
  return h ? { ...p, orig: p.src, src: h.src, w: h.w, h: h.h, full: h.full, fw: h.fw, fh: h.fh } : { ...p, orig: p.src };
};
export const articles = ([...(articlesJson as Article[]), ...(extraArticles as Article[])])
  .map((a) => ({ ...a, photos: a.photos.map(upgrade) }))
  .sort((a, b) => a.order - b.order);
const allPhotos = articles.flatMap((a) => a.photos);

// ---- Album : sections par lieu (dossiers envoyés), puis photos des récits absentes de ces dossiers
type AlbumPhoto = { id: string; src: string; full: string; w: number; h: number; date: string | null; article: string | null };
type AlbumSection = { place: string; from: string | null; to: string | null; photos: AlbumPhoto[] };
const albumData = albumJson as Record<string, AlbumSection[]>;
export type AlbumGroup = { title: string; from?: string | null; to?: string | null; link?: { href: string; label: string }; photos: Photo[] };
// photos de récits déjà présentes dans les dossiers de l'album (correspondance faite par album.py)
const inAlbum = new Set(albumIndex as string[]);
export function albumGroups(rubrique: string): AlbumGroup[] {
  const secs = splitByStop(albumData[rubrique] ?? [], rubrique);
  const groups: AlbumGroup[] = secs.map((s) => ({
    title: s.place, from: s.from, to: s.to,
    photos: s.photos.map((p) => ({ src: p.src, w: p.w, h: p.h, full: p.full, fw: p.w, fh: p.h, alt: captions[p.id] ?? s.place, caption: captions[p.id], date: p.date })),
  }));
  for (const a of articles.filter((x) => x.rubrique === rubrique)) {
    const rest = a.photos.filter((p) => !inAlbum.has(p.orig ?? p.src));
    if (rest.length) groups.push({ title: secs.length ? `Autres photos du récit « ${a.title} »` : a.title, link: { href: `/recit/${a.slug}/`, label: 'Lire le récit' }, photos: rest });
  }
  return groups;
}
/** Un dossier couvrant tout un pays (beaucoup de photos) est découpé par étape, d'après la date de chaque photo */
function splitByStop(secs: AlbumSection[], rubrique: string): AlbumSection[] {
  const mine = new Set((articlesJson as Article[]).filter((a) => a.rubrique === rubrique).map((a) => a.slug));
  const all = (itineraryJson as Stop[]).slice().sort((a, b) => a.date.localeCompare(b.date));
  const own = all.filter((st) => !st.transit && st.article && mine.has(st.article));
  const stops = own.length ? own : all;
  const out: AlbumSection[] = [];
  for (const s of secs) {
    if (s.photos.length < 40) { out.push(s); continue; }
    let cur: AlbumSection | null = null;
    for (const p of s.photos) {
      const d = (p.date ?? '').slice(0, 10);
      const stop = [...stops].reverse().find((st) => st.date <= d) ?? stops[0];
      // plusieurs étapes le même jour : on les nomme toutes (ex. lagunes du Sud Lípez)
      const sameDay = [...new Set(stops.filter((st) => st.date === stop.date).map((st) => st.name))];
      const name = sameDay.length > 3 ? `${sameDay.slice(0, 3).join(', ')}…` : sameDay.join(', ');
      if (!cur || cur.place !== name) { cur = { place: name, from: p.date, to: p.date, photos: [] }; out.push(cur); }
      cur.photos.push(p); cur.to = p.date;
    }
  }
  // fusion des petits morceaux (moins de 3 photos) avec la section précédente
  const merged: AlbumSection[] = [];
  for (const s of out) {
    const prev = merged[merged.length - 1];
    if (prev && (s.photos.length < 3 || prev.place === s.place)) { prev.photos.push(...s.photos); prev.to = s.to; }
    else merged.push(s);
  }
  return merged;
}
export const albumCount = (r: string) => albumGroups(r).reduce((n, g) => n + g.photos.length, 0);

const rubriquesAll: Rubrique[] = [...(rubriquesJson as Rubrique[])];
// rubrique « Le blog de Garance », retrouvée dans les archives (avec ses commentaires)
rubriquesAll.splice(rubriquesAll.findIndex((r) => r.slug === 'conclusion'), 0,
  { slug: 'blog-de-garance', name: 'Le blog de Garance', continent: null, num: 20, cover: null, articles: ['mon-blog'], photoCount: 0 });
export const rubriques = rubriquesAll.map((r) => {
  const src = (coversJson as Record<string, string>)[r.slug];
  const cover = src ? allPhotos.find((p) => p.orig === src) : undefined;
  const fallback = r.cover ?? albumGroups(r.slug)[0]?.photos[0] ?? null;
  const base = { ...r, cover: cover ?? fallback };
  return { ...base, photoCount: albumCount(r.slug) };
});
export const itinerary = itineraryJson as Stop[];

export const SITE = {
  title: 'Tout autour de la terre…',
  short: 'tdma4',
  tagline: '316 jours pour faire le tour du monde',
  family: 'Christine, Laurent, Antoine et Garance',
  description:
    "Le récit de notre tour du monde en famille, de septembre 2007 à juillet 2008 : Tanzanie, Chine, Laos, Cambodge, Bali, Australie, Nouvelle-Zélande, Polynésie, Île de Pâques, Patagonie, Chili, Bolivie, Pérou et États-Unis.",
};

export const articleBySlug = (s: string) => articles.find((a) => a.slug === s)!;
export const rubriqueBySlug = (s: string) => rubriques.find((r) => r.slug === s)!;
export const articlesOf = (r: string) => articles.filter((a) => a.rubrique === r);
export const countryRubriques = rubriques.filter((r) => r.continent);

const fmt = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
const fmtShort = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', timeZone: 'UTC' });
const fmtMonth = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric', timeZone: 'UTC' });
export const formatDate = (iso: string) => fmt.format(new Date(iso + 'T00:00:00Z'));
export const formatShort = (iso: string) => fmtShort.format(new Date(iso + 'T00:00:00Z'));
export const formatMonth = (iso: string) => fmtMonth.format(new Date(iso + 'T00:00:00Z'));

/** Jour du voyage (1 = 17 septembre 2007) */
export const dayOfTrip = (iso: string) =>
  Math.round((Date.parse(iso + 'T00:00:00Z') - Date.parse('2007-09-17T00:00:00Z')) / 86400000) + 1;

/** Période couverte par une rubrique, d'après l'itinéraire réel */
export function rubriquePeriod(slug: string): string | null {
  const slugs = new Set(articlesOf(slug).map((a) => a.slug));
  const stops = itinerary.filter((s) => s.article && slugs.has(s.article));
  if (!stops.length) return null;
  const a = stops[0].date, b = stops[stops.length - 1].date;
  const ma = formatMonth(a), mb = formatMonth(b);
  if (ma === mb) return ma;
  const [ya, yb] = [a.slice(0, 4), b.slice(0, 4)];
  const monthOnly = (iso: string) => new Intl.DateTimeFormat('fr-FR', { month: 'long', timeZone: 'UTC' }).format(new Date(iso + 'T00:00:00Z'));
  return ya === yb ? `${monthOnly(a)} – ${mb}` : `${ma} – ${mb}`;
}

/** Rangées « justifiées » : 1→1, 2→2, 3→3, 4→2+2, 5→3+2, 6→3+3, 7→3+2+2 … */
export function rows<T>(items: T[]): T[][] {
  const n = items.length;
  if (n <= 3) return [items];
  const out: T[][] = [];
  let i = 0;
  let left = n;
  while (left > 0) {
    const take = left === 4 ? 2 : left === 2 ? 2 : left % 3 === 1 && left > 4 ? 3 : Math.min(3, left);
    out.push(items.slice(i, i + take));
    i += take;
    left -= take;
  }
  return out;
}

export const urls = {
  article: (s: string) => `/recit/${s}/`,
  rubrique: (s: string) => `/pays/${s}/`,
  album: (s?: string) => (s ? `/album/${s}/` : '/album/'),
};
