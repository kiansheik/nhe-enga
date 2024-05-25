<template>
  <div id="app">
    <div class="function-bank">
      <h3>Root Input</h3>
      <input v-model="wordbase" placeholder="root" type="text" />
      <h3>Function Bank</h3>
      <div
        v-for="fn in Object.keys(functions)"
        :key="fn"
        class="function-item"
        @dragstart="onDragStart($event, fn)"
        @click="addFunction(fn)"
        draggable
      >
        {{ fn }}
      </div>
    </div>
    <div
      class="builder"
      @dragover="onDragOver"
      @drop="onDrop"
    >
      <h3>Result</h3>
      <div class='result'><py :key="selectedFunctions.join('')+word" >{{ applyFunctions(word, selectedFunctions) }}</py></div>
      <h3>Builder</h3>
      <div
        v-for="(fn, index) in selectedFunctions"
        :key="index"
        class="builder-item"
      >
        {{ fn }}
        <button @click="removeFunction(index)">Remove</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      wordbase: 'mba\'e',
      selectedFunctions: [],
      // functionNames: ['xe', '-saba', 'remi-', "-a"],
      functions: {
        'remi-': (word) => word + '.emi()',
        '-sab': (word) => word + '.saba()',
        '-sar': (word) => word + '.sara()',
        "-ba'e": (word) => word + '.bae()',
        '-pyr': (word) => word + '.pyr()',
        '-reme': (word) => word + '.reme()',
        '-ram': (word) => word + '.ram()',
        '-puer': (word) => word + '.puer()',
        '-a': (word) => word + '.substantivo()',
      },
    };
  },
  computed: {
    word() {
      return 'Noun("' + this.wordbase + '", "v. intr.")';
    }
  },
  methods: {
    addFunction(fn) {
      this.selectedFunctions.push(fn);
    },
    onDragStart(event, functionName) {
      event.dataTransfer.setData('functionName', functionName);
    },
    onDragOver(event) {
      event.preventDefault();
    },
    onDrop(event) {
      const functionName = event.dataTransfer.getData('functionName');
      this.selectedFunctions.push(functionName);
    },
    removeFunction(index) {
      this.selectedFunctions.splice(index, 1);
    },
    applyFunctions(word, functions) {
      if (this.wordbase === '') word = 'Noun("mba\'e", "")';
      let ret = functions.reduce((acc, fn) => this.functions[fn](acc), word);
      if (ret.endsWith('.substantivo()')){
        return ret;
      } else {
        return ret + '.verbete()';
      }
    },
  },
};
</script>

<style scoped>
#app {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.function-bank, .builder {
  border: 1px solid black;
  padding: 10px;
  /* width: 100%; */
}

.function-item, .builder-item {
  border: 1px solid gray;
  padding: 5px;
  margin-bottom: 5px;
  cursor: move;
}

.builder-item button {
  margin-left: 10px;
}

/* Input styling */
input {
    width: 100%;
    padding: 12px 20px;
    margin: 8px 0;
    box-sizing: border-box;
    border: 2px solid #ccc;
    border-radius: 4px;
}

.result {
    font-size: 20px;
    width: 100%;
    padding: 12px 20px;
    margin: 8px 0;
    box-sizing: border-box;
    border: 2px solid #ccc;
    border-radius: 4px;
}
</style>
