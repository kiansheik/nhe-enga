let dataset = [
    { f: "Data not loaded...", m: "circunstancial", s: "ixé", o: "xé" },
    // Add more sentences and information here
];

let currentQuestionIndex = 0;
let score = 0;
let question_count = 5;

function startQuiz() {
    // Load the dataset from 'verbs.json'
    fetch('quiz.json')
        .then(response => response.json())
        .then(data => {
            // Assign the loaded data to the dataset variable
            dataset = data;

            // Shuffle the dataset
            shuffleDataset();

            // Populate dropdown options
            populateDropdown('mode', ['indicativo', 'permissivo', 'circunstancial', 'gerundio', 'imperativo']);
            populateDropdown('subject', ['ger.', 'ixé', 'oré', 'îandé', 'endé', "pe'ẽ", "a'e"]);
            populateDropdown('object', ['intr.', 'xé', 'oré', 'îandé', 'nde', "pe", "i"]);

            showQuestion();
        })
        .catch(error => {
            console.error('Error loading dataset:', error);
        });
}

function shuffleDataset() {
    for (let i = dataset.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [dataset[i], dataset[j]] = [dataset[j], dataset[i]];
    }
}

function populateDropdown(id, options) {
    const dropdown = document.getElementById(id);
    
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.text = option;
        dropdown.add(optionElement);
    });
}


function showQuestion() {
    if (currentQuestionIndex < question_count) {
        const currentQuestion = dataset[currentQuestionIndex];
        document.getElementById('question').innerText = currentQuestion.f;
    } else {
        showResult();
    }
}

function submitAnswer() {
    const mode = document.getElementById('mode').value;
    const subject = document.getElementById('subject').value;
    const object = document.getElementById('object').value;

    checkDropdownAnswer('mode', mode);
    checkDropdownAnswer('subject', subject);
    checkDropdownAnswer('object', object);

    // Move to the next question
    currentQuestionIndex++;
    resetDropdowns();
    showQuestion();
}

function resetDropdowns() {
    // Reset dropdowns to their default values
    document.getElementById('mode').value = '';
    document.getElementById('subject').value = '';
    document.getElementById('object').value = '';
}

let subj_pref_map = {
    'ger.': null,
    'ixé': '1ps',
    'oré': '1ppe',
    'îandé': '1ppi',
    'endé': '2ps',
    "pe'ẽ": '2pp',
    "a'e": '3p'
}
let obj_pref_map = {
    'intr.': null,
    'xé': '1ps',
    'oré': '1ppe',
    'îandé': '1ppi',
    'nde': '2ps',
    "pe": '2pp',
    "i": '3p'
} 

function checkDropdownAnswer(part, selectedValue) {
    const currentQuestion = dataset[currentQuestionIndex];
    // console.log(part, selectedValue, selectedValue.substring(0, 2), currentQuestion.m)
    if (part === 'mode' && selectedValue.substring(0, 2) === currentQuestion.m) {
        score++;
    } else if (part === 'subject' && subj_pref_map[selectedValue] === currentQuestion.s) {
        score++;
    } else if (part === 'object' && obj_pref_map[selectedValue] === currentQuestion.o) {
        score++;
    }
    console.log(score, currentQuestion);
}

function showResult() {
    document.getElementById('quiz-container').style.display = 'none';
    const resultContainer = document.getElementById('result-container');
    resultContainer.style.display = 'block';
    resultContainer.innerHTML = `<p>Your score is: ${score} out of ${question_count*3}</p>`;
}

document.addEventListener("DOMContentLoaded", function () {
    // Your JavaScript code here
    startQuiz();
    resetDropdowns();
});