<template>
    <span class="help-text" :title="content" onclick="swapTitleAndInnerText(event)">
     <slot></slot>
    </span>
 </template>
 <script>
 export default {
   props: ['content']
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
}

.help-text:hover {
    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2); /* Increase box shadow on hover */
}
</style>