<template>
        <div class="python-output" v-text="tText"></div>
</template>
    
<script>
// import { eventBus } from '../eventBus';
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
            otherComponentLoaded: pl.pyodideReady,
            pyLoader: pl,
            pyRendered: false,
            origText: this.$slots.default[0].text,
            tText: 'rendering...' // this.$slots.default[0].text // Add this line
        };
    },
    methods: {
        handleMessage(event) {
            // Check the command of the message
            if (event.data.command === 'processBlockResponse' && event.data.pre_html === this.origText) {
                // Handle the message
                this.tText = event.data.resp_html;
                this.pyRendered = true;
            }
        },
        updateContent() {
            if (this.pyRendered) {
                return;
            }
            // this.tText = this.origText;
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
                orderid: this.getCurrentComponentIndex(),
                html: this.origText // Send the transformed text as the HTML
            };

            // Send the message to the iframe
            if (iframe) {
                iframe.contentWindow.postMessage(message, '*');
            } else {
                console.log('no iframe 2')
            }
        },
        getAllPyComponents() {
            let pyComponents = [];

            // Get all <py> elements in the DOM order
            let pyElements = document.querySelectorAll('div.python-output');

            for (let element of pyElements) {
                    pyComponents.push(element);
            }

            return pyComponents;
        },
        getCurrentComponentIndex() {
            let allPyComponents = this.getAllPyComponents();
            // console.log(allPyComponents)
            // Return the index of the current component's div.python-output element in the array
            return allPyComponents.indexOf(this.$el);
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
    watch: {
        pyodideReady(newVal, oldVal) {
            if (newVal) {
                this.updateContent();
            }
        },
    },
    mounted() {
        window.addEventListener('message', this.handleMessage);
        if (this.pyodideReady) {
            this.updateContent();
        }
        // eventBus.$on('softNavigationFinished', (to, from) => {
        //     if (this.pyodideReady) {
        //         this.updateContent();
        //     }
        // });
    },
    beforeDestroy() {
        window.removeEventListener('message', this.handleMessage);
        // eventBus.$off('softNavigationFinished');
    },
}
</script>
<style>
.python-output {
    display: inline-block;
}
</style>
