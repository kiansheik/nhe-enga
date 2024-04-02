<template>
  <div :key="definition" @click="toggleDefinition" class="root-div">
    <div class="tupi-text">
      <!-- <client-only> -->
        <strong><py>n = Noun("{{this.root}}", "{{ this.definition }}".strip()); {{ this.inflection }}</py></strong>
    <!-- </client-only> -->
    </div>
    <div :class="{ 'hidden': this.hideDefinition, 'tupi-def': true }">
      <!-- <client-only> -->
        <py>n.raw_definition</py>
      <!-- </client-only> -->
    </div>
  </div>
</template>
<script>
  import py from './py.vue';
  // define function toBolean if not defined
  function toBoolean(value) {
    return !['0', 'false', '', 0, undefined, NaN].includes(value);
  }
  export default {
    name: 'root',
    components: {
      py
    },
    data() {
      let pl = {dictLoaded:false};
      let layoutComponent = this.$root.$refs.layout;
      if (layoutComponent && layoutComponent.$children.length > 0) {
          let firstChildComponent = layoutComponent.$children[0];
          if (firstChildComponent.$refs.pyLoader) {
              pl = firstChildComponent.$refs.pyLoader;
          } else {
              console.log('no pyLoader')
          }
      } else {
          console.log('no layoutComponent')
      }     
      return {
        hideDefinition: true,
        // dictLoaded: pl.dictLoaded,
        raw_definition: null,
        pyLoader: pl
      }
    },
    methods: {
      toggleDefinition() {
        if (window.getSelection().toString().length === 0) {
            // No text is selected, so toggle the definition
            this.hideDefinition = !this.hideDefinition;
        }
      },
      updateDefinition(){
        if (this.dictLoaded) {
          this.raw_definition = this.pyLoader.findDefinition(this.root, this.entryNumber);
        }
      }
    },
    props: {
      root: String,
      type: {
        type: String,
        default: 'root'
      },
      entryNumber: {
        type: String,
        default: ''
      },
      root: String,
      pluriform: {
        type: String,
        default: ''
      },
      transitive: {
        type: String,
        default: ''
      },
      secondClass: {
        type: String,
        default: ''
      },
      subjectTense: {
        type: String,
        default: '1ps'
      },
      objectTense:  {
        type: String,
        default: ''
      },
      obj:  {
        type: String,
        default: ''
      },
      subj:  {
        type: String,
        default: ''
      },
      mode: {
        type: String,
        default: 'indicativo'
      },
      pos: {
        type: String,
        default: 'anteposto'
      },
      proDrop: {
        type: String,
        default: ''
      },
      negative: {
        type: String,
        default: ''
      },
      anotated: {
        type: String,
        default: ''
      }
    },
    computed: {
      trans() {
        return toBoolean(this.transitive) ? "(v.tr.)" : "";
      },
      second() {
        return toBoolean(this.secondClass) ? "adj." : "";
      },
      anot() {
        return toBoolean(this.anotated) ? "True" : "False";
      },
      proD() {
        return toBoolean(this.proDrop) ? "True" : "False";
      },
      neg() {
        return toBoolean(this.negative) ? "True" : "False";
      },
      inflection() {
        switch (this.type) {
            case 'verb':
                let tl =  `n.conjugate("${this.subjectTense }", "${this.objectTense}", anotar=${this.anot}, pro_drop=${this.proD}, negative=${this.neg}, mode="${this.mode}", pos="${this.pos}", dir_obj_raw="${this.obj}", dir_subj_raw="${this.subj}")`
                return tl
                break;
            case 'noun':
                return `n.substantivo(anotated=${this.anot})`
                break;
            default:
                return `n.verbete(anotated=${this.anot})`
                break;
        }
      },
      definition() {
        return this.raw_definition || `${this.trans} ${this.pluriform} ${this.second}`;
      },
      dictLoaded() {
            let pl = {dictLoaded:false};
            let layoutComponent = this.$root.$refs.layout;
            if (layoutComponent && layoutComponent.$children.length > 0) {
                let firstChildComponent = layoutComponent.$children[0];
                if (firstChildComponent.$refs.pyLoader) {
                    pl = firstChildComponent.$refs.pyLoader;
                }
            }   
            return pl.dictLoaded;
        }
    },
    watch: {
      dictLoaded(newVal, oldVal) {
        if (newVal && !oldVal) {
          console.log('dict loaded! ', this)
          this.updateDefinition();
        }
      }
    },
    created() {
      this.updateDefinition();
    }
  }
</script>
<style>
.root-div {
    cursor: help;
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
}
.hidden {
    display: none;
}
.tupi-def {
    display: inline;
}
.tupi-def.hidden {
    display: none;
}
</style>