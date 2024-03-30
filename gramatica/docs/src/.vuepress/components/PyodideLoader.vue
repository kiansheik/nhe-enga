<template>
    <div>
        <iframe id="pyodide-iframe" :src="`${this.basePath}iframe_pyodide.html`" style="display: none;"></iframe>
    </div>
</template>
<script>
export default {
    data() {
        return {
            pyodideReady: false,
            basePath: this.env === '"development"' ? '/' : '/nhe-enga/gramatica/',
        };
    },
    computed: {
        env() {
            return this.$site.base;
        },
    },
    methods: {
        receiveMessage (event) {
            if (event.data.pyodideReady) {
                    console.log("pyodide ready!")
                    this.pyodideReady = true;
                    this.processPage();
                    
            }
        },
        processPage() {
            let block = document.querySelector('.page');
            let html = block.innerHTML;
            return new Promise((resolve, reject) => {
                // Post a message to the iframe
                const iframe = document.getElementById('pyodide-iframe');
                iframe.contentWindow.postMessage({
                    command: 'processBlock',
                    html: html
                }, '*');

                // Set up an event listener to receive the response
                const listener = (event) => {
                    if (event.data.command === 'processBlockResponse') {
                        // Remove the event listener once we receive the response
                        window.removeEventListener('message', listener);
                        block.innerHTML = event.data.html;
                        if (event.data.error) {
                            reject(new Error(event.data.error));
                        } else {
                            resolve(event.data.html);
                        }
                    }
                };
                window.addEventListener('message', listener);
            });
        },
    },
    mounted () {
        window.addEventListener('message', this.receiveMessage)
    },
    beforeDestroy () {
        window.removeEventListener('message', this.receiveMessage)
    }
};
</script>