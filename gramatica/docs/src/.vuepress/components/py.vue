<template>
    <div class="python-output" v-text="tText"></div>
</template>
    
<script>

export default {
    name: 'py',
    data() {
        // console.log(this.$root.$refs.layout.$children[0].$refs.pyLoader.pyodideReady)
        let pl = {pyodideReady:false};
        let layoutComponent = this.$root.$refs.layout;
        if (layoutComponent && layoutComponent.$children.length > 0) {
            let firstChildComponent = layoutComponent.$children[0];
            if (firstChildComponent.$refs.pyLoader) {
                pl = firstChildComponent.$refs.pyLoader;
                // Use pl here
            }
        }        
        return {
            otherComponentLoaded: pl.pyodideReady,
            pyLoader: pl,
            tText: 'rendering...' // this.$slots.default[0].text // Add this line
        };
    },
    methods: {
        handleMessage(event) {
            // Check the command of the message
            if (event.data.command === 'processBlockResponse' && event.data.pre_html === this.tText) {
                // Handle the message
                this.tText = event.data.resp_html;
            }
        },
        updateContent() {
            this.tText = this.$slots.default[0].text;
            // console.log(this.tText)
            let iframe;
            if (this.pyLoader && this.pyLoader.$refs && this.pyLoader.$refs.pyodideiframe) {
                iframe = this.pyLoader.$refs.pyodideiframe;
            // Use iframe here
            }
            // Create the message
            let message = {
                command: 'processBlock',
                orderid: this.getCurrentComponentIndex(),
                html: this.tText // Send the transformed text as the HTML
            };

            // Send the message to the iframe
            if (iframe) {
                iframe.contentWindow.postMessage(message, '*');
            }
        },
        getAllPyComponents() {
            let pyComponents = [];

            // Get all <py> elements in the DOM order
            let pyElements = document.querySelectorAll('div.python-output');

            for (let element of pyElements) {
                // Get the Vue component instance associated with the element
                // let component = this.$root.$el.__vue__;
                // if (component) {
                    pyComponents.push(element);
                // }
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
                    // Use pl here
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
        '$route': {
            immediate: false,
            handler: "updateContent"
        }
    },
    mounted() {
        window.addEventListener('message', this.handleMessage);
        if (this.pyodideReady) {
            this.updateContent();
        }
    },
    beforeDestroy() {
        window.removeEventListener('message', this.handleMessage);
    },
}
</script>
<style>
.python-output {
    display: inline-block;
}
</style>
