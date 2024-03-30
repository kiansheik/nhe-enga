import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Learn You Some Tupi Antigo for Great Good!",
  description: "A practical guide to Tupi Antigo grammar",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/guide/' }
    ],

    sidebar: [
      {
        text: 'Introduction',
        items: [
          { link: '/guide/' },
          { text: 'Roots', link: '/guide/roots' }
        ]
      },
      {
        text: 'Pronouns',
        items: [
          { text: 'Personal Pronouns', link: '/guide/pronouns/personal' },
        ]
      },
      {
        text: 'Verbs',
        items: [
          { text: 'Indicative Mood', link: '/guide/verbs/indicative' },
        ]
      },
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/kiansheik/nhe-enga' }
    ]
  }
})
