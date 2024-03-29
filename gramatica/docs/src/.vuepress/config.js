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
    // ['script', { src: "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js" }],
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
  markdown: {
    extractHeaders: ['h2', 'h3', 'h4', 'h5' , 'h6']
  },
  themeConfig: {
    repo: '',
    editLinks: false,
    docsDir: '',
    editLinkText: '',
    lastUpdated: false,
    algolia: false,
    nav: [
      {
        text: 'Guide',
        link: '/guide/',
      },
      {
        text: 'Dictionary',
        link: 'https://kiansheik.io/nhe-enga/',
      },
    ],
    sidebar: {
      '/guide/': [
        {
          title: 'Introduction',
          collapsable: true,
          displayAllHeaders: true,
          sidebarDepth: 6,
          children: [
            '',
            'roots'
          ]
        },
        {
          title: 'Pronouns',
          collapsable: true,
          displayAllHeaders: true,
          sidebarDepth: 6,
          children: [
            'pronouns/personal',
          ]
        },
        {
          title: 'Verbs',
          collapsable: true,
          sidebarDepth: 6,
          displayAllHeaders: true,
          children: [
            'verbs/indicative',
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
