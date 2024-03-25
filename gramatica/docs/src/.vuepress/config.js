const { description } = require('../../package')
const path = require('path');

module.exports = {
  /**
   * Ref：https://v1.vuepress.vuejs.org/config/#title
   */
  title: 'Tupi Antigo',
  /**
   * Ref：https://v1.vuepress.vuejs.org/config/#description
   */
  description: description,

  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
  },

  /**
   * Extra tags to be injected to the page HTML `<head>`
   *
   * ref：https://v1.vuepress.vuejs.org/config/#head
   */
  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#3eaf7c' }],
    ['meta', { name: 'apple-mobile-web-app-capable', content: 'yes' }],
    ['meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black' }],
    ['meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black' }],
    ['script', { src: "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js" }],
    // ['PyodideLoader'],
    // add an entry for PyodideLoader custom component
    ['script', { src: "/utility_funcs.js" }],
  ],

  /**
   * Theme configuration, here is the default theme configuration for VuePress.
   *
   * ref：https://v1.vuepress.vuejs.org/theme/default-theme-config.html
   */
  theme: path.resolve(__dirname, './theme/theme-default'),
  base: process.env.NODE_ENV === 'production' ? '/nhe-enga/gramatica/' : '/',
  themeConfig: {
    repo: '',
    editLinks: false,
    docsDir: '',
    editLinkText: '',
    lastUpdated: false,
    nav: [
      {
        text: 'Guide',
        link: '/guide/',
      },
    ],
    sidebar: {
      '/guide/': [
        {
          title: 'Guide',
          collapsable: true,
          sidebarDepth: 4,
          children: [
            '',
            'roots',
            'nouns',
            'conjugation',
            'indicative',
          ]
        }
      ],
    }
  },

  /**
   * Apply plugins，ref：https://v1.vuepress.vuejs.org/zh/plugin/
   */
  plugins: [
    '@vuepress/plugin-back-to-top',
    '@vuepress/plugin-medium-zoom',
  ]
}
