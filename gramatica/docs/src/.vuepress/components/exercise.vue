<template>
  <div class="exercise-container">
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
    /* font-family: 'Georgia', serif; */
    color: #6C6C2A; 
    background-color: #F8F8E1;
    border: 1.2px solid #6C6C2A; 
    padding-left: 3px;
    padding-right: 3px;
    padding-top: 0px;
    padding-bottom: 1px;
    border-radius: 7px;
    font-family: "Arial"
}
</style>