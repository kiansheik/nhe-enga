(window["webpackJsonp"] = window["webpackJsonp"] || []).push([[25],{

/***/ "./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/PyodideLoader.vue?vue&type=script&lang=js":
/*!****************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/cache-loader/dist/cjs.js??ref--3-0!./node_modules/babel-loader/lib??ref--3-1!./node_modules/cache-loader/dist/cjs.js??ref--0-0!./node_modules/vue-loader/lib??vue-loader-options!./src/.vuepress/components/PyodideLoader.vue?vue&type=script&lang=js ***!
  \****************************************************************************************************************************************************************************************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var core_js_modules_es_error_cause_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! core-js/modules/es.error.cause.js */ "./node_modules/core-js/modules/es.error.cause.js");
/* harmony import */ var core_js_modules_es_error_cause_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_es_error_cause_js__WEBPACK_IMPORTED_MODULE_0__);

/* harmony default export */ __webpack_exports__["default"] = ({
  data() {
    return {
      pyodideReady: false,
      basePath: this.env === '"development"' ? '/' : '/nhe-enga/gramatica/'
    };
  },
  computed: {
    env() {
      return this.$site.base;
    }
  },
  methods: {
    receiveMessage(event) {
      if (event.data.pyodideReady) {
        console.log("pyodide ready!");
        this.pyodideReady = true;
        this.processPage();
      }
    },
    processPage() {
      let block = document.querySelector('.page');
      let html = block.innerHTML;
      return new Promise((resolve, reject) => {
        // Post a message to the iframe
        const iframe = document.getElementById('pyodide-iframe');
        iframe.contentWindow.postMessage({
          command: 'processBlock',
          html: html
        }, '*');

        // Set up an event listener to receive the response
        const listener = event => {
          if (event.data.command === 'processBlockResponse') {
            // Remove the event listener once we receive the response
            window.removeEventListener('message', listener);
            block.innerHTML = event.data.html;
            if (event.data.error) {
              reject(new Error(event.data.error));
            } else {
              resolve(event.data.html);
            }
          }
        };
        window.addEventListener('message', listener);
      });
    }
  },
  mounted() {
    window.addEventListener('message', this.receiveMessage);
  },
  beforeDestroy() {
    window.removeEventListener('message', this.receiveMessage);
  }
});

/***/ }),

/***/ "./node_modules/cache-loader/dist/cjs.js?{\"cacheDirectory\":\"node_modules/@vuepress/core/node_modules/.cache/vuepress\",\"cacheIdentifier\":\"4c95426e-vue-loader-template\"}!./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=4a7022da":
/*!*************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/cache-loader/dist/cjs.js?{"cacheDirectory":"node_modules/@vuepress/core/node_modules/.cache/vuepress","cacheIdentifier":"4c95426e-vue-loader-template"}!./node_modules/cache-loader/dist/cjs.js??ref--3-0!./node_modules/babel-loader/lib??ref--3-1!./node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!./node_modules/cache-loader/dist/cjs.js??ref--0-0!./node_modules/vue-loader/lib??vue-loader-options!./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=4a7022da ***!
  \*************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "render", function() { return render; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "staticRenderFns", function() { return staticRenderFns; });
var render = function render() {
  var _vm = this,
    _c = _vm._self._c;
  return _c('div', [_c('iframe', {
    staticStyle: {
      "display": "none"
    },
    attrs: {
      "id": "pyodide-iframe",
      "src": `${this.basePath}iframe_pyodide.html`
    }
  })]);
};
var staticRenderFns = [];


/***/ }),

/***/ "./src/.vuepress/components/PyodideLoader.vue":
/*!****************************************************!*\
  !*** ./src/.vuepress/components/PyodideLoader.vue ***!
  \****************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _PyodideLoader_vue_vue_type_template_id_4a7022da__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./PyodideLoader.vue?vue&type=template&id=4a7022da */ "./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=4a7022da");
/* harmony import */ var _PyodideLoader_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./PyodideLoader.vue?vue&type=script&lang=js */ "./src/.vuepress/components/PyodideLoader.vue?vue&type=script&lang=js");
/* empty/unused harmony star reexport *//* harmony import */ var _node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../node_modules/vue-loader/lib/runtime/componentNormalizer.js */ "./node_modules/vue-loader/lib/runtime/componentNormalizer.js");





/* normalize component */

var component = Object(_node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__["default"])(
  _PyodideLoader_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_1__["default"],
  _PyodideLoader_vue_vue_type_template_id_4a7022da__WEBPACK_IMPORTED_MODULE_0__["render"],
  _PyodideLoader_vue_vue_type_template_id_4a7022da__WEBPACK_IMPORTED_MODULE_0__["staticRenderFns"],
  false,
  null,
  null,
  null
  
)

/* harmony default export */ __webpack_exports__["default"] = (component.exports);

/***/ }),

/***/ "./src/.vuepress/components/PyodideLoader.vue?vue&type=script&lang=js":
/*!****************************************************************************!*\
  !*** ./src/.vuepress/components/PyodideLoader.vue?vue&type=script&lang=js ***!
  \****************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_PyodideLoader_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../node_modules/cache-loader/dist/cjs.js??ref--3-0!../../../node_modules/babel-loader/lib??ref--3-1!../../../node_modules/cache-loader/dist/cjs.js??ref--0-0!../../../node_modules/vue-loader/lib??vue-loader-options!./PyodideLoader.vue?vue&type=script&lang=js */ "./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/PyodideLoader.vue?vue&type=script&lang=js");
/* empty/unused harmony star reexport */ /* harmony default export */ __webpack_exports__["default"] = (_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_PyodideLoader_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_0__["default"]); 

/***/ }),

/***/ "./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=4a7022da":
/*!**********************************************************************************!*\
  !*** ./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=4a7022da ***!
  \**********************************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _node_modules_cache_loader_dist_cjs_js_cacheDirectory_node_modules_vuepress_core_node_modules_cache_vuepress_cacheIdentifier_4c95426e_vue_loader_template_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_vue_loader_lib_loaders_templateLoader_js_ref_6_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_PyodideLoader_vue_vue_type_template_id_4a7022da__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../node_modules/cache-loader/dist/cjs.js?{"cacheDirectory":"node_modules/@vuepress/core/node_modules/.cache/vuepress","cacheIdentifier":"4c95426e-vue-loader-template"}!../../../node_modules/cache-loader/dist/cjs.js??ref--3-0!../../../node_modules/babel-loader/lib??ref--3-1!../../../node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!../../../node_modules/cache-loader/dist/cjs.js??ref--0-0!../../../node_modules/vue-loader/lib??vue-loader-options!./PyodideLoader.vue?vue&type=template&id=4a7022da */ "./node_modules/cache-loader/dist/cjs.js?{\"cacheDirectory\":\"node_modules/@vuepress/core/node_modules/.cache/vuepress\",\"cacheIdentifier\":\"4c95426e-vue-loader-template\"}!./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=4a7022da");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "render", function() { return _node_modules_cache_loader_dist_cjs_js_cacheDirectory_node_modules_vuepress_core_node_modules_cache_vuepress_cacheIdentifier_4c95426e_vue_loader_template_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_vue_loader_lib_loaders_templateLoader_js_ref_6_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_PyodideLoader_vue_vue_type_template_id_4a7022da__WEBPACK_IMPORTED_MODULE_0__["render"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "staticRenderFns", function() { return _node_modules_cache_loader_dist_cjs_js_cacheDirectory_node_modules_vuepress_core_node_modules_cache_vuepress_cacheIdentifier_4c95426e_vue_loader_template_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_vue_loader_lib_loaders_templateLoader_js_ref_6_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_PyodideLoader_vue_vue_type_template_id_4a7022da__WEBPACK_IMPORTED_MODULE_0__["staticRenderFns"]; });



/***/ })

}]);
//# sourceMappingURL=25.78415a76.js.map