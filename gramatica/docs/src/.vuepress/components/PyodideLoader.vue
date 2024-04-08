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
            pyodideLoaded: false,
            dictLoaded: false,
            evBus: eventBus,
            basePath: NODE_ENV !== 'development' ? '/nhe-enga/gramatica/' : '/',
            elems: [], // New data property to store the messages
            jsonData: null,
        };
    },
    methods: {
        async loadJson() {
            try {
                const response = await fetch('/nhe-enga/docs/dict-conjugated.json');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const json = await response.json();
                this.jsonData = json;
                this.dictLoaded = true;
                console.log('dict loaded!')
                if (this.pyodideLoaded) {
                    this.pyodideReady = true;
                    this.updateContent();
                }
            } catch (error) {
                console.error('There was a problem loading the JSON file:', error);
            }
        },
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
            if (event.data.pyodideLoaded) {
                this.pyodideLoaded = true;
                console.log("pyodide Loaded!");
                // console.log("comps: "+ this.countComponents())
                if (this.dictLoaded) {
                    this.pyodideReady = true;
                    this.updateContent();
                }
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
                let elem = allPyComponents[cidx];
                // if (elem.$parent.$options._componentTag === 'root') {
                //     elem.$parent.updateDefinition();
                // }
                // elem.updateDefinition();
                let message = {
                    command: 'processBlock',
                    orderid: cidx,
                    hash: elem.hash,
                    html: elem.origText // Send the transformed text as the HTML
                };
                this.$refs.pyodideiframe.contentWindow.postMessage(message, '*');
            }
            // if (soft){
            //     this.elems = [];
            // }
        },
        findDefinition(root, optionalNumber) {
            optionalNumber = optionalNumber || '';
            // for entry in this.jsonData
            for (let entry of this.jsonData) {
                if (entry.f === root && entry.o === optionalNumber) {
                    return entry.d.replace(/"/g, '\\"');
                }
            }
            return null;
        },
    },
    created() {
        this.loadJson();
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