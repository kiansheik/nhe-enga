<template>
    <div>
      <p v-if="showAnswer" class="answer">{{ content }}</p>
      <input
        v-model="guess"
        @keyup.enter="checkAnswer"
        :class="{ correct: isCorrect, incorrect: isIncorrect }"
        type="text"
        placeholder="Guess!"
      />
    </div>
  </template>
  
  <script>
  export default {
    props: {
      content: {
        type: String,
        required: true,
      },
    },
    data() {
      return {
        guess: '',
        isCorrect: false,
        isIncorrect: false,
        showAnswer: false,
      };
    },
    methods: {
      checkAnswer() {
        console.log(this.guess)
        if (this.guess === this.content) {
          this.isCorrect = true;
          this.isIncorrect = false;
          this.showAnswer = false;
        } else {
          this.isCorrect = false;
          this.isIncorrect = true;
          this.showAnswer = true;
        }
      },
    },
  };
  </script>
  
  <style scoped>
    .correct {
    background-color: rgba(76, 175, 80, 0.3); /* Light Green */
    }
    .incorrect {
    background-color: rgba(244, 67, 54, 0.3); /* Light Red */
    }
    .answer {
    color: rgba(244, 67, 54, 0.7); /* Translucent Red */
    }
  </style>