import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://tdma4.pages.dev',
  trailingSlash: 'always',
  integrations: [sitemap()],
  build: { inlineStylesheets: 'auto', assets: 'assets' },
});
