// Compteur de visites public, sans cookie.
// Base Cloudflare D1 liée sous le nom DB (Pages > Paramètres > Liaisons). Sans base, le compteur reste masqué.
// GET : renvoie le total ; POST : compte une nouvelle visite (le navigateur ne l'envoie qu'une fois par session).
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });

async function ready(db) {
  await db.prepare('CREATE TABLE IF NOT EXISTS compteur (id INTEGER PRIMARY KEY, n INTEGER NOT NULL)').run();
  await db.prepare('INSERT OR IGNORE INTO compteur (id, n) VALUES (1, 0)').run();
}

export async function onRequestGet({ env }) {
  if (!env.DB) return json({ error: 'indisponible' }, 503);
  await ready(env.DB);
  const row = await env.DB.prepare('SELECT n FROM compteur WHERE id = 1').first();
  return json({ visites: row?.n ?? 0 });
}

export async function onRequestPost({ env, request }) {
  if (!env.DB) return json({ error: 'indisponible' }, 503);
  // on ne compte que les appels venant du site lui-même, et pas les robots déclarés
  const origin = request.headers.get('origin');
  const ua = request.headers.get('user-agent') || '';
  if ((origin && new URL(origin).host !== new URL(request.url).host) || /bot|crawl|spider|preview/i.test(ua)) {
    return onRequestGet({ env });
  }
  await ready(env.DB);
  const row = await env.DB.prepare('UPDATE compteur SET n = n + 1 WHERE id = 1 RETURNING n').first();
  return json({ visites: row?.n ?? 0 });
}
