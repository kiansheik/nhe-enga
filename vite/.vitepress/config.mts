import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Tupi Antigo Grammar",
  description: "An English Grammar of Tupi Antigo",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/guide/' }
    ],

    sidebar: [
      {
        text: 'Guide',
        items: [
          { text: 'Introduction', link: '/guide/' },
          { text: 'Roots', link: '/guide/roots' },
          { text: 'Nouns', link: '/guide/nouns' },
          { text: 'Conjugations', link: '/guide/conjugation' },
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/kiansheik/nhe-enga' }
    ]
  }
})
