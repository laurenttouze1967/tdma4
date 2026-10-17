// Carte du monde en projection Equal Earth (résolution ONU « Correct the Map »),
// calculée une fois pour toutes au moment de la construction du site.
import { geoEqualEarth, geoPath, geoGraticule10, geoInterpolate } from 'd3-geo';
import { feature, mesh } from 'topojson-client';
import world from 'world-atlas/countries-110m.json';
import { itinerary } from './data';

export const WIDTH = 1000;
const topo = world as any;
const countries = feature(topo, topo.objects.countries) as any;
const borders = mesh(topo, topo.objects.countries, (a: any, b: any) => a !== b);

const projection = geoEqualEarth().fitWidth(WIDTH, { type: 'Sphere' } as any);
const path = geoPath(projection);
const [, [, y1]] = path.bounds({ type: 'Sphere' } as any);
export const HEIGHT = Math.ceil(y1);

// Pays traversés (codes ISO numériques)
const VISITED = new Set(['250', '834', '156', '418', '116', '360', '036', '554', '152', '032', '068', '604', '840']);

export const sphere = path({ type: 'Sphere' } as any)!;
export const graticule = path(geoGraticule10())!;
export const land = countries.features.map((f: any) => ({ d: path(f)!, visited: VISITED.has(String(f.id).padStart(3, '0')) }));
export const borderPath = path(borders)!;

const round = (n: number) => Math.round(n * 10) / 10;

/** Tracé d'un tronçon : arc de grand cercle (découpé au besoin à l'antiméridien).
 *  Les vols sont en plus bombés sur le côté (à droite du sens de la marche) : un aller-retour
 *  en avion dessine ainsi deux arcs distincts au lieu de se superposer comme une route. */
function legPath(proj: any, a: [number, number], b: [number, number], mode: string | null, pathGen: any) {
  const coords = densify(a, b);
  const line = { type: 'LineString', coordinates: coords } as any;
  if (mode !== 'avion') return pathGen(line) ?? '';
  const pts = coords.map((c) => proj(c) as [number, number] | null);
  if (pts.some((p) => !p) || pts.some((p, k) => k && Math.hypot(p![0] - pts[k - 1]![0], p![1] - pts[k - 1]![1]) > WIDTH / 3)) {
    return pathGen(line) ?? '';
  }
  const [x0, y0] = pts[0]!, [x1, y1] = pts[pts.length - 1]!;
  const L = Math.hypot(x1 - x0, y1 - y0);
  if (L < 1) return pathGen(line) ?? '';
  const nx = -(y1 - y0) / L, ny = (x1 - x0) / L;
  const h = Math.min(0.14 * L, 70);
  const n = pts.length - 1;
  return 'M' + pts.map((p, k) => {
    const f = 4 * (k / n) * (1 - k / n) * h;
    return `${round(p![0] + nx * f)},${round(p![1] + ny * f)}`;
  }).join('L');
}
const legMode = (m: string | null | undefined) => (m === 'bus' ? 'route' : (m ?? 'route'));

export const legs = itinerary.slice(1).map((stop, i) => {
  const from = itinerary[i];
  return { d: legPath(projection, [from.lon, from.lat], [stop.lon, stop.lat], stop.mode, path), mode: legMode(stop.mode), index: i + 1 };
});

function densify(a: [number, number], b: [number, number]) {
  const interp = geoInterpolate(a, b);
  const n = 24;
  return Array.from({ length: n + 1 }, (_, k) => interp(k / n));
}

export const points = itinerary.map((s, i) => {
  const [x, y] = projection([s.lon, s.lat])!;
  return { ...s, x: round(x), y: round(y), index: i };
});

// ---- Vues régionales (zoom par continent) -------------------------------------
// Fond de carte plus détaillé (1/50 000 000), projection Equal Earth recentrée sur la région.
import world50 from 'world-atlas/countries-50m.json';
const topo50 = world50 as any;
const countries50 = feature(topo50, topo50.objects.countries) as any;
const borders50 = mesh(topo50, topo50.objects.countries, (a: any, b: any) => a !== b);

export const VIEW_H = 600;
export const REGIONS: { key: string; label: string; countries: string[] }[] = [
  { key: 'afrique', label: 'Afrique', countries: ['Tanzanie', 'Kenya', 'Afrique du Sud'] },
  { key: 'asie', label: 'Asie', countries: ['Chine', 'Laos', 'Cambodge', 'Malaisie', 'Indonésie'] },
  { key: 'oceanie', label: 'Océanie', countries: ['Australie', 'Nouvelle-Zélande', 'Polynésie française'] },
  { key: 'amerique-sud', label: 'Amérique du Sud', countries: ['Chili', 'Argentine', 'Bolivie', 'Pérou'] },
  { key: 'amerique-nord', label: 'Amérique du Nord', countries: ['États-Unis'] },
];
export const regionOf = (country: string) => REGIONS.find((r) => r.countries.includes(country))?.key ?? 'monde';

export const regionViews = REGIONS.map((r) => {
  const pts = itinerary.filter((s) => r.countries.includes(s.country) && !s.transit);
  const lons = pts.map((p) => p.lon);
  // longitude centrale (gère le passage de l'antiméridien en Océanie)
  const unwrapped = lons.map((l) => (r.key === 'oceanie' && l < 0 ? l + 360 : l));
  const center = (Math.min(...unwrapped) + Math.max(...unwrapped)) / 2;
  const proj = geoEqualEarth().rotate([-center, 0]);
  const pad = 44;
  // étendue minimale (≈ 24° × 14°) pour garder un peu de contexte autour d'un petit pays
  const coords: [number, number][] = pts.map((p) => [p.lon, p.lat]);
  const lats = pts.map((p) => p.lat);
  const midLat = (Math.min(...lats) + Math.max(...lats)) / 2;
  const span = Math.max(...unwrapped) - Math.min(...unwrapped);
  if (span < 24) coords.push([center - 12, midLat], [center + 12, midLat]);
  if (Math.max(...lats) - Math.min(...lats) < 14) coords.push([center, midLat - 7], [center, midLat + 7]);
  proj.fitExtent([[pad, pad], [WIDTH - pad, VIEW_H - pad]], { type: 'MultiPoint', coordinates: coords } as any);
  proj.clipExtent([[-20, -20], [WIDTH + 20, VIEW_H + 20]]);
  const p = geoPath(proj);
  const landR = countries50.features
    .map((f: any) => ({ d: p(f) ?? '', visited: VISITED.has(String(f.id).padStart(3, '0')) }))
    .filter((c: any) => c.d);
  const legsR = itinerary.slice(1).map((stop, i) => {
    const from = itinerary[i];
    return { d: legPath(proj, [from.lon, from.lat], [stop.lon, stop.lat], stop.mode, p), mode: legMode(stop.mode), index: i + 1 };
  });
  const ptsR = itinerary.map((s, i) => {
    const xy = proj([s.lon, s.lat]);
    const inside = !!xy && xy[0] > -30 && xy[0] < WIDTH + 30 && xy[1] > -30 && xy[1] < VIEW_H + 30;
    return { x: xy ? round(xy[0]) : -999, y: xy ? round(xy[1]) : -999, inside, index: i };
  });
  return { key: r.key, label: r.label, graticule: p(geoGraticule10()) ?? '', land: landR, borders: p(borders50) ?? '', legs: legsR, points: ptsR };
});
