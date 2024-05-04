<template>
    <Tooltip content="consonant"><py>' '.join(Noun.consoantes)</py></Tooltip>
  </template>
  
  <script>
  import Tooltip from './Tooltip.vue';
  
  export default {
    name: 'tConsonants',
    components: {
      Tooltip
    }
  }
  </script>