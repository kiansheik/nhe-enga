(window["webpackJsonp"] = window["webpackJsonp"] || []).push([[27],{

/***/ "./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/PyodideLoader.vue?vue&type=script&lang=js":
/*!****************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/cache-loader/dist/cjs.js??ref--3-0!./node_modules/babel-loader/lib??ref--3-1!./node_modules/cache-loader/dist/cjs.js??ref--0-0!./node_modules/vue-loader/lib??vue-loader-options!./src/.vuepress/components/PyodideLoader.vue?vue&type=script&lang=js ***!
  \****************************************************************************************************************************************************************************************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
// import { base } from '../config.js';

/* harmony default export */ __webpack_exports__["default"] = ({
  data() {
    return {
      pyodideReady: false,
      basePath:  false ? undefined : '/nhe-enga/gramatica/'
    };
  },
  methods: {
    receiveMessage(event) {
      if (event.data.pyodideReady) {
        console.log("pyodide ready!");
        this.pyodideReady = true;
      }
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

/***/ "./node_modules/cache-loader/dist/cjs.js?{\"cacheDirectory\":\"node_modules/@vuepress/core/node_modules/.cache/vuepress\",\"cacheIdentifier\":\"4c95426e-vue-loader-template\"}!./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=861c28de":
/*!*************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/cache-loader/dist/cjs.js?{"cacheDirectory":"node_modules/@vuepress/core/node_modules/.cache/vuepress","cacheIdentifier":"4c95426e-vue-loader-template"}!./node_modules/cache-loader/dist/cjs.js??ref--3-0!./node_modules/babel-loader/lib??ref--3-1!./node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!./node_modules/cache-loader/dist/cjs.js??ref--0-0!./node_modules/vue-loader/lib??vue-loader-options!./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=861c28de ***!
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
    ref: "pyodideiframe",
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
/* harmony import */ var _PyodideLoader_vue_vue_type_template_id_861c28de__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./PyodideLoader.vue?vue&type=template&id=861c28de */ "./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=861c28de");
/* harmony import */ var _PyodideLoader_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./PyodideLoader.vue?vue&type=script&lang=js */ "./src/.vuepress/components/PyodideLoader.vue?vue&type=script&lang=js");
/* empty/unused harmony star reexport *//* harmony import */ var _node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../node_modules/vue-loader/lib/runtime/componentNormalizer.js */ "./node_modules/vue-loader/lib/runtime/componentNormalizer.js");





/* normalize component */

var component = Object(_node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__["default"])(
  _PyodideLoader_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_1__["default"],
  _PyodideLoader_vue_vue_type_template_id_861c28de__WEBPACK_IMPORTED_MODULE_0__["render"],
  _PyodideLoader_vue_vue_type_template_id_861c28de__WEBPACK_IMPORTED_MODULE_0__["staticRenderFns"],
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

/***/ "./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=861c28de":
/*!**********************************************************************************!*\
  !*** ./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=861c28de ***!
  \**********************************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _node_modules_cache_loader_dist_cjs_js_cacheDirectory_node_modules_vuepress_core_node_modules_cache_vuepress_cacheIdentifier_4c95426e_vue_loader_template_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_vue_loader_lib_loaders_templateLoader_js_ref_6_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_PyodideLoader_vue_vue_type_template_id_861c28de__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../node_modules/cache-loader/dist/cjs.js?{"cacheDirectory":"node_modules/@vuepress/core/node_modules/.cache/vuepress","cacheIdentifier":"4c95426e-vue-loader-template"}!../../../node_modules/cache-loader/dist/cjs.js??ref--3-0!../../../node_modules/babel-loader/lib??ref--3-1!../../../node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!../../../node_modules/cache-loader/dist/cjs.js??ref--0-0!../../../node_modules/vue-loader/lib??vue-loader-options!./PyodideLoader.vue?vue&type=template&id=861c28de */ "./node_modules/cache-loader/dist/cjs.js?{\"cacheDirectory\":\"node_modules/@vuepress/core/node_modules/.cache/vuepress\",\"cacheIdentifier\":\"4c95426e-vue-loader-template\"}!./node_modules/cache-loader/dist/cjs.js?!./node_modules/babel-loader/lib/index.js?!./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/cache-loader/dist/cjs.js?!./node_modules/vue-loader/lib/index.js?!./src/.vuepress/components/PyodideLoader.vue?vue&type=template&id=861c28de");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "render", function() { return _node_modules_cache_loader_dist_cjs_js_cacheDirectory_node_modules_vuepress_core_node_modules_cache_vuepress_cacheIdentifier_4c95426e_vue_loader_template_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_vue_loader_lib_loaders_templateLoader_js_ref_6_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_PyodideLoader_vue_vue_type_template_id_861c28de__WEBPACK_IMPORTED_MODULE_0__["render"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "staticRenderFns", function() { return _node_modules_cache_loader_dist_cjs_js_cacheDirectory_node_modules_vuepress_core_node_modules_cache_vuepress_cacheIdentifier_4c95426e_vue_loader_template_node_modules_cache_loader_dist_cjs_js_ref_3_0_node_modules_babel_loader_lib_index_js_ref_3_1_node_modules_vue_loader_lib_loaders_templateLoader_js_ref_6_node_modules_cache_loader_dist_cjs_js_ref_0_0_node_modules_vue_loader_lib_index_js_vue_loader_options_PyodideLoader_vue_vue_type_template_id_861c28de__WEBPACK_IMPORTED_MODULE_0__["staticRenderFns"]; });



/***/ })

}]);
//# sourceMappingURL=27.b7b67f0c.js.map