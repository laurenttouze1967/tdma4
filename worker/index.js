// Point d'entrée Cloudflare Workers : sert le site statique (dossier dist) et les deux petites API.
import * as contact from '../functions/api/contact.js';
import * as visites from '../functions/api/visites.js';

const API = { '/api/contact': contact, '/api/visites': visites };

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    const mod = API[pathname.replace(/\/$/, '')];
    if (mod) {
      const handler = mod[`onRequest${request.method[0]}${request.method.slice(1).toLowerCase()}`] ?? mod.onRequest;
      if (!handler) return new Response('Méthode non autorisée', { status: 405 });
      return handler({ request, env });
    }
    return env.ASSETS.fetch(request);
  },
};
