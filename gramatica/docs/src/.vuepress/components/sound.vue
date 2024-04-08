<template>
    <div class="sound-container">
      <button @click="playAudio">
        {{ this.sound }}
      </button>
      <audio ref="audioRef">
        <source :src="formattedAudioSource" type="audio/mp3">
        Your browser does not support the audio element.
      </audio>
    </div>
  </template>
  
  <script>
  export default {
    name: 'sound',
    props: {
      sound: {
        type: String,
        required: true,
      }
    },
    computed: {
      formattedAudioSource() {
        return `/nhe-enga/pronunciation/${this.sound}.mp3`;
      }
    },
    methods: {
      playAudio() {
        this.$refs.audioRef.play();
      }
    }
  }
  </script>
  
  <style scoped>
  .sound-container {
    display: inline-block;
    background-color: transparent;
    border: none;
    padding: 0;
  }
  
  button {
  display: inline-block;
  color: #FFFFFF;
  background-color: #008CBA; /* Brighter blue background */
  border: none;
  padding: 0px 11px; /* Larger padding */
  border-radius: 24px; /* Rounded corners */
  cursor: pointer; /* Pointer/hand icon */
  font-size: 25px; /* Larger font size */
  font-family: 'Cinzel', serif;
  box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2), 0 6px 20px 0 rgba(0,0,0,0.19); /* Add shadows */
}

button:hover {
  background-color: #007B9A; /* Darker blue on hover */
}
  </style>