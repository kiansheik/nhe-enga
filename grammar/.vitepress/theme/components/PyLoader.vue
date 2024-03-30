<template>
    <div>
        <iframe id="pyodide-iframe" ref="pyodideiframe" :src="`${this.basePath}iframe_pyodide.html`" style="display: none;"></iframe>
    </div>
</template>
<script>
export default {
    data() {
        return {
            pyodideReady: false,
            basePath: process.env.NODE_ENV !== '"development"' ? '/nhe-enga/gramatica/' : '/',
        };
    },
    methods: {
        receiveMessage (event) {
            if (event.data.pyodideReady) {
                    console.log("pyodide ready!")
                    this.pyodideReady = true;
                    
            }
        },
    },
    mounted () {
        window.addEventListener('message', this.receiveMessage)
    },
    beforeDestroy () {
        window.removeEventListener('message', this.receiveMessage)
    },
};
</script>