<template>
    <div>
        <iframe id="pyodide-iframe" ref="pyodideiframe" :src="`${this.basePath}iframe_pyodide.html`" style="display: none;"></iframe>
    </div>
</template>
<script>
import { eventBus } from './eventBus.js';

export default {
    data() {
        return {
            pyodideReady: false,
            evBus: eventBus,
            basePath: NODE_ENV !== 'development' ? '/nhe-enga/gramatica/' : '/',
            elems: [], // New data property to store the messages
        };
    },
    methods: {
        getAllPyComponents() {
            return Array.from(document.querySelectorAll('.python-output'));
        },
        getCurrentComponentIndex(element) {
            let allPyComponents = this.getAllPyComponents();
            // console.log(allPyComponents)
            // Return the index of the current component's div.python-output element in the array
            return allPyComponents.indexOf(element);
        },
        countComponents() {
            return this.getAllPyComponents().length;
        },
        receiveMessage (event) {
            if (event.data.pyodideReady) {
                console.log("pyodide ready!");
                this.pyodideReady = true;
                // console.log("comps: "+ this.countComponents())
                this.updateContent();
            } 
        },
        sendMessagesToIframe() {
            for (let message of this.messages) {
                // Send message.command to the iframe
                this.$refs.pyodideiframe.contentWindow.postMessage(message.command, '*');
            }
        },
        updateContent(soft){
            // Create the message
            // console.log("updating");
            let allPyComponents = this.getAllPyComponents().map(el => el.__vue__);
            for (let cidx = 0; cidx < allPyComponents.length; cidx++) {
                let message = {
                    command: 'processBlock',
                    orderid: cidx,
                    hash: allPyComponents[cidx].hash,
                    html: allPyComponents[cidx].origText // Send the transformed text as the HTML
                };
                this.$refs.pyodideiframe.contentWindow.postMessage(message, '*');
            }
            // if (soft){
            //     this.elems = [];
            // }
        }
    },
    mounted () {
        this.evBus.$on("pyReadyRender", (element, idx) => {
            this.elems.push(element);
            let cnt = this.countComponents();
            // console.log('EMITED: ' + element.origText, cnt, idx, this.elems.length);
            if (this.pyodideReady && this.elems.length >= cnt) {
                this.updateContent(true);
            }
        })
        window.addEventListener('message', this.receiveMessage)
    },
    beforeDestroy () {
        window.removeEventListener('message', this.receiveMessage)
    },
};
</script>