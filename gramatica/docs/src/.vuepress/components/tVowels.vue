<template>
    <Tooltip content="%' '.join(n.vogais)%">vowel</Tooltip>
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