<template>
    <div>
        <div v-if="env !== '/'">
            <script>
                let basePath = '/nhe-enga/gramatica/';
            </script>
        </div>
        <div v-else>
            <script>
                let basePath = '/';
            </script>
        </div>
        <script>
            let globalPyodide, pyodideReady = false;
            window.pyodideReady = false;

            async function initializePython() {
                globalPyodide = await loadPyodide();
                console.log(globalPyodide.runPython(`
                    import sys
                    sys.version
                `));
                await globalPyodide.loadPackage('micropip');
                const micropip = globalPyodide.pyimport('micropip');
                await micropip.install(`${basePath}pylibs/tupi-0.1.0-py3-none-any.whl`);
                console.log('Package installed');
                globalPyodide.runPython('import tupi');
                globalPyodide.runPython('print(tupi.Noun(\'îagûar\', \'normal\'))');
                pyodideReady = true;
                window.pyodideReady = pyodideReady;
                blocks = document.querySelectorAll('.page');
                blocks.forEach(function(block) {
                    block.innerHTML = block.innerHTML.replace(/\%(.*?)\%/g, function(_, match) {
                    // Your custom JavaScript goes here
                    console.log(match)
                    if (match === '(.*?)\\')
                        return match
                    return globalPyodide.runPython('from tupi import Noun; '+ match); // For example, convert the text to uppercase
                    });
                });
                return globalPyodide;
            }
            initializePython();
        </script>
    </div>
</template>

<script>
export default {
    computed: {
        env() {
            return this.$site.base;
        }
    },
//   data() {
//     return {
//         'env': this.$site.base
//     }
//   }
};
</script>