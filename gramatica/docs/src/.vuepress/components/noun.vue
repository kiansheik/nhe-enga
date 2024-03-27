<template>
    <py>n = Noun("{{this.root}}", "{{ this.trans }} {{ this.pluriform }} {{ this.second }}".strip()); {{ this.inflection }}</py>
    </template>
<script>
  import py from './py.vue';
  function toBoolean(value) {
    return !['0', 'false', '', 0, undefined, NaN].includes(value);
    }
  export default {
    name: 'noun',
    components: {
      py
    },
    props: {
      root: String,
      type: {
        type: String,
        default: 'root'
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
                let tl =  `n.conjugate("${this.subjectTense }", "${this.objectTense}", anotar="${this.anot}", pro_drop=${this.proD}, negative=${this.neg}, mode="${this.mode}", pos="${this.pos}", dir_obj_raw="${this.obj}", dir_subj_raw="${this.subj}")`
                console.log(tl)
                return tl
                break;
            case 'noun':
                return `n.substantivo(anotated=${this.anot})`
                break;
            default:
                return `n.verbete(anotated=${this.anot})`
                break;
        }
      }
    },
    // methods: {
    //   conjugate() {
    //     // Implement the conjugate method here
    //   }
    // },
    // mounted() {
    //   this.conjugate();
    // }
  }
</script>
<style>
.tupi-text {
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
</style>