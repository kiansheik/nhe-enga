<template>
  <p class="demo">
    {{ msg }}
  </p>
</template>

<script>
  export default {
    data() {
      return {
        msg: 'Hello this is <demo-component>'
      }
    },
    mounted() {
      this.$nextTick(function () {
        // Code that will run only after the
        // entire view has been rendered
        const demoComponent = document.querySelector('demo-component');
        if (demoComponent) {
          console.log(demoComponent.textContent);
        }
      })
    }
  }
</script>