<template>
  <div class="exercise-container">
    <div class="practice-header">Practice</div>
    <div class="question-box">
      <!-- <client-only> -->
        <slot></slot>
    <!-- </client-only> -->
    </div>
    <div class="response-box">
      <!-- <client-only> -->
        <wQuiz :answer="this.answer"></wQuiz>
      <!-- </client-only> -->
    </div>
  </div>
</template>
<script>
import wQuiz from './wQuiz.vue';
// define function toBolean if not defined
function toBoolean(value) {
    return !['0', 'false', '', 0, undefined, NaN].includes(value);
}
export default {
    name: 'exercise',
    components: {
        wQuiz
    },
    props: {
      answer: {
        type: String,
        required: true,
      },
    },
}
</script>
<style>
.exercise-container {
    display: inline-block;
    color: #6C6C2A; 
    background-color: #F8F8E1;
    border: 1.2px solid #6C6C2A; 
    padding-left: 3px;
    padding-right: 3px;
    padding-top: 0px;
    padding-bottom: 1px;
    border-radius: 7px;
    font-family: "Arial";
    overflow: hidden; /* Hide overflow */
}

.practice-header {
    font-size: 0.9em; 
    font-weight: bold; 
    color: #767c70; 
    border: 1px solid #8C8C4A; 
    background-color: #edf8e1; 
    position: relative; /* Relative to the parent container */
    left: -9px;
    width: calc(100% + 14px);
    padding-left: 9px; /* Offset the text to the right */
    padding-right: 9px; /* Offset the text to the left */
}
</style>