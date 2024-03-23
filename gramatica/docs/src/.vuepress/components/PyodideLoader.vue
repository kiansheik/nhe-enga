<template>
    <div v-if="pyodideLoaded">
      <slot></slot>
      <script>
        blocks = document.querySelectorAll('.page');
        blocks.forEach(block => {
            block.innerHTML = block.innerHTML.replace(/\%(.*?)\%/g, (_, match) => {
            // Your custom JavaScript goes here
            return window.plo.runPython('from tupi import Noun; '+ match); // For example, convert the text to uppercase
            });
        });
      </script>
    </div>
    <div v-else>
      Loading data, please wait a moment...
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        pyodideLoaded: false
      };
    },
    mounted() {
      this.loadPyodide();
    },
    methods: {
      async loadPyodide() {
        if (typeof window.plo === 'undefined') {
            window.plo = await loadPyodide();
            await window.plo.loadPackage('micropip');
            const micropip = window.plo.pyimport('micropip');
            await micropip.install('../dist/tupi-0.1.0-py3-none-any.whl');
            window.plo.runPython('from tupi import Noun; ');
            console.log('Package installed');
        }
        this.pyodideLoaded = true;
      }
    }
  };
  </script>