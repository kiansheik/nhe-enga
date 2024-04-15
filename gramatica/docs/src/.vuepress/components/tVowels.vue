<template>
    <Tooltip content="vowel"><py>' '.join(Noun.vogais)</py></Tooltip>
  </template>
  
  <script>
  import Tooltip from './Tooltip.vue';
  
  export default {
    name: 'tVowels',
    components: {
      Tooltip
    }
  }
  </script>