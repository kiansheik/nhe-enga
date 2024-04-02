<template>
    <div class="help-text" @click="toggleDefinition">
        <span :class="{ 'hidden': this.show}">
            {{ this.content }}
        </span>
        <span :class="{ 'hidden': !this.show}">
            <slot></slot>
        </span>
    </div>
 </template>
 <script>
 export default {
   props: ['content'],
   data() {
        return {
            show: false
        }
    },
    methods: {
      toggleDefinition() {
        if (window.getSelection().toString().length === 0) {
            // No text is selected, so toggle the definition
            this.show = !this.show;
        }
      },
    }
 }
 </script>
<style scoped>
.help-text {
    cursor: help;
    border: 1px solid #888; /* Add a border */
    padding: 2px 5px; /* Add some padding */
    background-color: #f9f9f9; /* Add a background color */
    box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1); /* Add a box shadow for depth */
    transition: box-shadow 0.3s ease; /* Add a transition for smoothness */
    border-radius: 5px; /* Add rounded corners */
    white-space: nowrap; /* Prevent line breaks within the span */
    display: inline-block; /* Move the entire span to a new line instead of breaking */
    animation: glow 2s infinite; /* Add a glow animation */
}

.help-text:hover {
    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2); /* Increase box shadow on hover */
}

span.hidden {
    display: none;
}

/* Define the glow animation */
@keyframes glow {
    0% { box-shadow: 0 0 0px #add8e5, 0 0 0px #add8e6; }
    50% { box-shadow: 0 0 1px #add8e6, 0 0 4px #add8e6; }
    100% { box-shadow: 0 0 0px #add8e6, 0 0 0px #add8e6; }
}
</style>