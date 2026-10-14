import articlesJson from '../data/articles.json';
import rubriquesJson from '../data/rubriques.json';
import itineraryJson from '../data/itinerary.json';
import coversJson from '../data/covers.json';

export type Photo = { src: string; w: number; h: number; alt: string };
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
  name: string; country: string; lat: number; lon: number; date: string; dateApprox: boolean;
  mode: 'avion' | 'bateau' | 'route' | 'train' | null; article: string | null; note: string;
};

export const articles = (articlesJson as Article[]).slice().sort((a, b) => a.order - b.order);
const allPhotos = (articlesJson as Article[]).flatMap((a) => a.photos);
export const rubriques = (rubriquesJson as Rubrique[]).map((r) => {
  const src = (coversJson as Record<string, string>)[r.slug];
  const cover = src ? allPhotos.find((p) => p.src === src) : undefined;
  return cover ? { ...r, cover } : r;
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
