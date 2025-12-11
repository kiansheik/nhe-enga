<template>
  <div id="app">
    <div class="function-bank">
      <h3>Root Input</h3>
      <input v-model="wordbase" placeholder="root" type="text" />
      <div>
        <label class="custom-checkbox" >
          <input type="checkbox" v-model="transitivity" />
          <span class="checkmark"></span>
          Transitive
        </label>
        <label class="custom-checkbox" >
          <input type="checkbox" v-model="secondClass" />
          <span class="checkmark"></span>
          Second Class
        </label>
        <label class="custom-checkbox" >
          <input type="checkbox" v-model="pluriform" />
          <span class="checkmark"></span>
          Pluriform
        </label>
      </div>
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
      transitivity: false,
      secondClass: false,
      pluriform: false,
      selectedFunctions: [],
      // functionNames: ['xe', '-saba', 'remi-', "-a"],
      functions: {
        'xe (possessive)': (word) => word + '.possessive("1ps")',
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
      let definition = '';
      if (this.transitivity) definition += '(v. tr.) ';
      if (this.secondClass) definition += '(2ª classe) ';
      if (this.pluriform) definition += '(t) ';
      // If there is a ' ' in wordbase
      if (this.wordbase.includes('-')) {
        // split on ' ' 
        let words = this.wordbase.split('-');
        return `Noun("${words[0]}", "${definition}").compose( Noun("${words[1]}", "${definition}") )`;
      }
      return `Noun("${this.wordbase}", "${definition}")`;
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
    background-color: #fef9c3;
}

/* Checkmarks */

.custom-checkbox {
  position: relative;
  padding-left: 22px;
  cursor: pointer;
  font-size: 12px;
  user-select: none;
}

.custom-checkbox input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  position: absolute;
  top: 0;
  left: 0;
  height: 20px;
  width: 20px;
  background-color: #eee;
}

.custom-checkbox input:checked ~ .checkmark {
  background-color: #2196F3;
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
}

.custom-checkbox input:checked ~ .checkmark:after {
  display: block;
}

.custom-checkbox .checkmark:after {
  left: 6px;
  top: 3px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 3px 3px 0;
  transform: rotate(45deg);
}

</style>
