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

/** Un tronçon entre deux étapes : arc de grand cercle, découpé au besoin à l'antiméridien */
export const legs = itinerary.slice(1).map((stop, i) => {
  const from = itinerary[i];
  const line = { type: 'LineString', coordinates: densify([from.lon, from.lat], [stop.lon, stop.lat]) } as any;
  return { d: path(line) ?? '', mode: stop.mode ?? 'route', index: i + 1 };
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
