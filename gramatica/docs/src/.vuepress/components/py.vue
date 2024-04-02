<template>
        <div :hash=hash class="python-output" v-text="tText"></div>
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
            // if (this.pyRendered) {
            //     return;
            // }
            let cidx = this.getCurrentComponentIndex()
            if (cidx < 0) {
                return;
            }
            // console.log("comps "+cidx+`: `+ this.countComponents()+ ` ${this.origText}`)
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
            // console.log(allPyComponents)
            // Return the index of the current component's div.python-output element in the array
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
    // watch: {
    //     pyodideReady(newVal, oldVal) {
    //         if (newVal && !oldVal) {
    //             this.$nextTick(() => {
    //                 if (this.pyodideReady) {
    //                     this.updateContent();
    //                 }
    //             });
    //         }
    //     },
    // },
    mounted() {
        window.addEventListener('message', this.handleMessage);
        // this.$nextTick(() => {
        //     if (this.pyodideReady) {
        //         this.updateContent();
        //     }
        // });
        this.alertReady();
    },
    beforeDestroy() {
        window.removeEventListener('message', this.handleMessage);
        this.pyLoader.elems = [];
    },
}
</script>
<style>
.python-output {
    display: inline-block;
}
</style>
