// import DefaultLayout from './theme/theme-default/layouts/Layout.vue';
import { eventBus } from './eventBus';

export default ({
  Vue, // the version of Vue being used in the VuePress app
  options, // the options for the root Vue instance
  router, // the router instance for the app
  siteData // site metadata
}) => {
  router.afterEach((to, from) => {
    Vue.nextTick(() => {
      eventBus.$emit('softNavigationFinished', to, from);
    });
  });
}