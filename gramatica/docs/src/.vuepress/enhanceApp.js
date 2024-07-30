/**
 * Client app enhancement file.
 *
 * https://v1.vuepress.vuejs.org/guide/basic-config.html#app-level-enhancements
 */

export default ({
  Vue, // the version of Vue being used in the VuePress app
  options, // the options for the root Vue instance
  router, // the router instance for the app
  siteData // site metadata
}) => {
  // Google Analytics integration
  if (process.env.NODE_ENV === 'production' && typeof window !== 'undefined') {
    // Create script tag for Google Analytics
    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=G-DZYY8Y9076';
    document.head.appendChild(script);

    script.onload = () => {
      window.dataLayer = window.dataLayer || [];
      function gtag() {
        window.dataLayer.push(arguments);
      }
      gtag('js', new Date());
      gtag('config', 'G-DZYY8Y9076');

      // Track page views on route change
      router.afterEach((to) => {
        gtag('config', 'G-DZYY8Y9076', { page_path: to.fullPath });
      });
    };
  }

  // ...apply other enhancements for the site.
}
