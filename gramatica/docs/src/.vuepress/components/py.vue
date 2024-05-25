<template>
        <div :hash=hash class="python-output" v-html="tText"></div>
</template>
    
<script>
// import { eventBus } from './eventBus.js';
// import { ClientOnly } from 'vue';

export default {
    // components: { ClientOnly },
    name: 'py',
    data() {
        let pl = {pyodideReady:false};
        let layoutComponent = this.$root.$refs.layout;
        if (layoutComponent && layoutComponent.$children.length > 0) {
            let firstChildComponent = layoutComponent.$children[0];
            if (firstChildComponent.$refs.pyLoader) {
                pl = firstChildComponent.$refs.pyLoader;
            } else {
                console.log('no pyLoader')
            }
        } else {
            console.log('no layoutComponent')
        }  
        return {
            pyLoader: pl,
            pyRendered: false,
            // Make a random hash for the component
            hash: Math.random().toString(36),
            evBus: pl.evBus,
            origText: this.$slots.default[0].text,
            tText: 'rendering...' // this.$slots.default[0].text // Add this line
        };
    },
    methods: {
        handleMessage(event) {
            // Check the command of the message
            if (event.data.command === 'processBlockResponse' && event.data.pre_html === this.origText && event.data.hash === this.hash) {
                // Handle the message
                this.tText = event.data.resp_html;
                this.pyRendered = true;
            }
        },
        updateContent() {
            let cidx = this.getCurrentComponentIndex()
            if (cidx < 0) {
                return;
            }
            this.tText = this.origText;
            let iframe;
            if (this.pyLoader && this.pyLoader.$refs && this.pyLoader.$refs.pyodideiframe) {
                iframe = this.pyLoader.$refs.pyodideiframe;
            // Use iframe here
            } else {
                console.log('no iframe')
            }
            // Create the message
            let message = {
                command: 'processBlock',
                orderid: cidx,
                html: this.origText, // Send the transformed text as the HTML
                hash: this.hash
            };

            // Send the message to the iframe
            if (iframe) {
                iframe.contentWindow.postMessage(message, '*');
            } else {
                console.log('no iframe 2')
            }
        },
        getAllPyComponents() {
            return Array.from(document.querySelectorAll('.python-output'));
        },
        getCurrentComponentIndex() {
            let allPyComponents = this.getAllPyComponents();
            return allPyComponents.indexOf(this.$el);
        },
        countComponents() {
            return this.getAllPyComponents().length;
        },
        alertReady() {
            if (this.getCurrentComponentIndex() >= 0) {
                this.evBus.$emit('pyReadyRender', this, this.getCurrentComponentIndex());
            }
        }
    },
    computed: {
        pyodideReady() {
            let pl = {pyodideReady:false};
            let layoutComponent = this.$root.$refs.layout;
            if (layoutComponent && layoutComponent.$children.length > 0) {
                let firstChildComponent = layoutComponent.$children[0];
                if (firstChildComponent.$refs.pyLoader) {
                    pl = firstChildComponent.$refs.pyLoader;
                }
            }   
            return pl.pyodideReady;
        }
    },
    mounted() {
        window.addEventListener('message', this.handleMessage);
        this.alertReady();
    },
    beforeDestroy() {
        window.removeEventListener('message', this.handleMessage);
        this.pyLoader.elems = [];
    },
}
</script>
<style>
/* @import url('https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800&family=Righteous&display=swap'); */
.python-output {
    display: inline-block;
}
</style>
