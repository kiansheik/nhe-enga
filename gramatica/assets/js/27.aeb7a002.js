(window["webpackJsonp"] = window["webpackJsonp"] || []).push([[27],{

/***/ "./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/py.vue?vue&type=script&lang=js":
/*!*****************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/cache-loader/dist/cjs.js??ref--3-0!./node_modules/babel-loader/lib??ref--3-1!./node_modules/cache-loader/dist/cjs.js??ref--0-0!./node_modules/vue-loader/lib??vue-loader-options!./src/.vuepress/components/py.vue?vue&type=script&lang=js ***!
  \*****************************************************************************************************************************************************************************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ({
  name: 'py',
  data() {
    // console.log(this.$root.$refs.layout.$children[0].$refs.pyLoader.pyodideReady)
    let pl = {
      pyodideReady: false
    };
    let layoutComponent = this.$root.$refs.layout;
    if (layoutComponent && layoutComponent.$children.length > 0) {
      let firstChildComponent = layoutComponent.$children[0];
      if (firstChildComponent.$refs.pyLoader) {
        pl = firstChildComponent.$refs.pyLoader;
        // Use pl here
      }
    }
    return {
      otherComponentLoaded: pl.pyodideReady,
      pyLoader: pl,
      tText: 'rendering...' // this.$slots.default[0].text // Add this line
    };
  },
  methods: {
    handleMessage(event) {
      // Check the command of the message
      if (event.data.command === 'processBlockResponse' && event.data.pre_html === this.tText) {
        // Handle the message
        this.tText = event.data.resp_html;
      }
    },
    updateContent() {
      this.tText = this.$slots.default[0].text;
      console.log(this.tText);
      let iframe;
      if (this.pyLoader && this.pyLoader.$refs && this.pyLoader.$refs.pyodideiframe) {
        iframe = this.pyLoader.$refs.pyodideiframe;
        // Use iframe here
      }
      // Create the message
      let message = {
        command: 'processBlock',
        html: this.tText // Send the transformed text as the HTML
      };

      // Send the message to the iframe
      if (iframe) {
        iframe.contentWindow.postMessage(message, '*');
      }
    }
  },
  computed: {
    pyodideReady() {
      let pl = {
        pyodideReady: false
      };
      let layoutComponent = this.$root.$refs.layout;
      if (layoutComponent && layoutComponent.$children.length > 0) {
        let firstChildComponent = layoutComponent.$children[0];
        if (firstChildComponent.$refs.pyLoader) {
          pl = firstChildComponent.$refs.pyLoader;
          // Use pl here
        }
      }
      return pl.pyodideReady;
    }
  },
  watch: {
    pyodideReady(newVal, oldVal) {
      if (newVal) {
        this.updateContent();
      }
    }
  },
  mounted() {
    window.addEventListener('message', this.handleMessage);
    if (this.pyodideReady) {
      this.updateContent();
    }
  },
  beforeDestroy() {
    window.removeEventListener('message', this.handleMessage);
  }
});

/***/ }),

/***/ "./node_modules/cache-loader/dist/cjs.js?{\"cacheDirectory\":\"node_modules/@vuepress/core/node_modules/.cache/vuepress\",\"cacheIdentifier\":\"4c95426e-vue-loader-template\"}!./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/py.vue?vue&type=template&id=5f613cf6":
/*!**************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/cache-loader/dist/cjs.js?{"cacheDirectory":"node_modules/@vuepress/core/node_modules/.cache/vuepress","cacheIdentifier":"4c95426e-vue-loader-template"}!./node_modules/cache-loader/dist/cjs.js??ref--3-0!./node_modules/babel-loader/lib??ref--3-1!./node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!./node_modules/cache-loader/dist/cjs.js??ref--0-0!./node_modules/vue-loader/lib??vue-loader-options!./src/.vuepress/components/py.vue?vue&type=template&id=5f613cf6 ***!
  \**************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "render", function() { return render; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "staticRenderFns", function() { return staticRenderFns; });
var render = function render() {
  var _vm = this,
    _c = _vm._self._c;
  return _c('div', {
    staticClass: "tupi-text",
    domProps: {
      "textContent": _vm._s(_vm.tText)
    }
  });
};
var staticRenderFns = [];


/***/ }),

/***/ "./src/.vuepress/components/py.vue":
/*!*****************************************!*\
  !*** ./src/.vuepress/components/py.vue ***!
  \*****************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _py_vue_vue_type_template_id_5f613cf6__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./py.vue?vue&type=template&id=5f613cf6 */ "./src/.vuepress/components/py.vue?vue&type=template&id=5f613cf6");
/* harmony import */ var _py_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./py.vue?vue&type=script&lang=js */ "./src/.vuepress/components/py.vue?vue&type=script&lang=js");
/* empty/unused harmony star reexport *//* harmony import */ var _node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../node_modules/vue-loader/lib/runtime/componentNormalizer.js */ "./node_modules/vue-loader/lib/runtime/componentNormalizer.js");





/* normalize component */

var component = Object(_node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__["default"])(
  _py_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_1__["default"],
  _py_vue_vue_type_template_id_5f613cf6__WEBPACK_IMPORTED_MODULE_0__["render"],
  _py_vue_vue_type_template_id_5f613cf6__WEBPACK_IMPORTED_MODULE_0__["staticRenderFns"],
  false,
  null,
  null,
  null
  
)

/* harmony default export */ __webpack_exports__["default"] = (component.exports);

/***/ }),

/***/ "./src/.vuepress/components/py.vue?vue&type=script&lang=js":
/*!*****************************************************************!*\
  !*** ./src/.vuepress/components/py.vue?vue&type=script&lang=js ***!
  \*****************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_py_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../node_modules/cache-loader/dist/cjs.js??ref--3-0!../../../node_modules/babel-loader/lib??ref--3-1!../../../node_modules/cache-loader/dist/cjs.js??ref--0-0!../../../node_modules/vue-loader/lib??vue-loader-options!./py.vue?vue&type=script&lang=js */ "./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/py.vue?vue&type=script&lang=js");
/* empty/unused harmony star reexport */ /* harmony default export */ __webpack_exports__["default"] = (_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_py_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_0__["default"]); 

/***/ }),

/***/ "./src/.vuepress/components/py.vue?vue&type=template&id=5f613cf6":
/*!***********************************************************************!*\
  !*** ./src/.vuepress/components/py.vue?vue&type=template&id=5f613cf6 ***!
  \***********************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _node_modules_cache_loader_dist_cjs_js_cacheDirectory_node_modules_vuepress_core_node_modules_cache_vuepress_cacheIdentifier_4c95426e_vue_loader_template_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_vue_loader_lib_loaders_templateLoader_js_ref_6_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_py_vue_vue_type_template_id_5f613cf6__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../node_modules/cache-loader/dist/cjs.js?{"cacheDirectory":"node_modules/@vuepress/core/node_modules/.cache/vuepress","cacheIdentifier":"4c95426e-vue-loader-template"}!../../../node_modules/cache-loader/dist/cjs.js??ref--3-0!../../../node_modules/babel-loader/lib??ref--3-1!../../../node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!../../../node_modules/cache-loader/dist/cjs.js??ref--0-0!../../../node_modules/vue-loader/lib??vue-loader-options!./py.vue?vue&type=template&id=5f613cf6 */ "./node_modules/cache-loader/dist/cjs.js?{\"cacheDirectory\":\"node_modules/@vuepress/core/node_modules/.cache/vuepress\",\"cacheIdentifier\":\"4c95426e-vue-loader-template\"}!./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/py.vue?vue&type=template&id=5f613cf6");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "render", function() { return _node_modules_cache_loader_dist_cjs_js_cacheDirectory_node_modules_vuepress_core_node_modules_cache_vuepress_cacheIdentifier_4c95426e_vue_loader_template_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_vue_loader_lib_loaders_templateLoader_js_ref_6_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_py_vue_vue_type_template_id_5f613cf6__WEBPACK_IMPORTED_MODULE_0__["render"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "staticRenderFns", function() { return _node_modules_cache_loader_dist_cjs_js_cacheDirectory_node_modules_vuepress_core_node_modules_cache_vuepress_cacheIdentifier_4c95426e_vue_loader_template_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_vue_loader_lib_loaders_templateLoader_js_ref_6_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_py_vue_vue_type_template_id_5f613cf6__WEBPACK_IMPORTED_MODULE_0__["staticRenderFns"]; });



/***/ })

}]);
//# sourceMappingURL=27.aeb7a002.js.map