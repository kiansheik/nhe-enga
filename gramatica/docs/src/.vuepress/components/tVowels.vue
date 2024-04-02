<template>
    <Tooltip content="<py>' '.join(n.vogais)</py>">vowel</Tooltip>
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