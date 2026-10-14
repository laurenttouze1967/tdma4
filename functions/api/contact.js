// Cloudflare Pages Function : POST /api/contact
// Reçoit le formulaire, vérifie Turnstile (anti-robots) et envoie le message par e-mail via Resend.
//
// Variables à définir dans Cloudflare Pages > Settings > Variables and Secrets :
//   CONTACT_TO        adresse qui reçoit les messages (jamais visible sur le site)
//   RESEND_API_KEY    clé API Resend (secret)
//   TURNSTILE_SECRET  clé secrète Turnstile (secret)
//   CONTACT_FROM      (facultatif) expéditeur, par défaut « tdma4 <onboarding@resend.dev> »

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json; charset=utf-8' } });

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

export async function onRequestPost({ request, env }) {
  const wantsJson = (request.headers.get('accept') || '').includes('application/json');
  const fail = (msg, status = 400) =>
    wantsJson ? json({ ok: false, error: msg }, status) : Response.redirect(new URL('/contact/?erreur=1', request.url), 303);

  let form;
  try { form = await request.formData(); } catch { return fail('Formulaire illisible.'); }
  const name = (form.get('name') || '').toString().trim().slice(0, 100);
  const email = (form.get('email') || '').toString().trim().slice(0, 200);
  const subject = (form.get('subject') || '').toString().trim().slice(0, 150);
  const message = (form.get('message') || '').toString().trim().slice(0, 5000);

  // Pot de miel : un robot remplit ce champ invisible
  if ((form.get('website') || '').toString()) return wantsJson ? json({ ok: true }) : Response.redirect(new URL('/contact/merci/', request.url), 303);

  if (!name || !message || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    return fail('Merci de remplir votre nom, une adresse e-mail valide et votre message.');
  }

  // Vérification Turnstile
  if (env.TURNSTILE_SECRET) {
    const body = new FormData();
    body.append('secret', env.TURNSTILE_SECRET);
    body.append('response', (form.get('cf-turnstile-response') || '').toString());
    body.append('remoteip', request.headers.get('CF-Connecting-IP') || '');
    const check = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body })
      .then((r) => r.json()).catch(() => ({ success: false }));
    if (!check.success) return fail('La vérification anti-robots a échoué. Rechargez la page et réessayez.', 403);
  }

  if (!env.RESEND_API_KEY || !env.CONTACT_TO) return fail("Le formulaire n'est pas encore configuré.", 503);

  const html = `<p><strong>${esc(name)}</strong> &lt;${esc(email)}&gt; a écrit depuis le site tdma4 :</p>
<p><em>${esc(subject || '(sans sujet)')}</em></p>
<blockquote style="border-left:3px solid #e2733f;padding-left:12px;margin-left:0">${esc(message).replace(/\n/g, '<br>')}</blockquote>
<p style="color:#888;font-size:12px">Répondez directement à ce message pour écrire à ${esc(name)}.</p>`;

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from: env.CONTACT_FROM || 'tdma4 <onboarding@resend.dev>',
      to: [env.CONTACT_TO],
      reply_to: email,
      subject: `[tdma4] ${subject || 'Message de ' + name}`,
      html,
      text: `${name} <${email}>\n${subject}\n\n${message}`,
    }),
  });
  if (!res.ok) return fail("Le message n'a pas pu être envoyé. Réessayez plus tard.", 502);
  return wantsJson ? json({ ok: true }) : Response.redirect(new URL('/contact/merci/', request.url), 303);
}

export const onRequest = () => new Response('Méthode non autorisée', { status: 405, headers: { Allow: 'POST' } });
