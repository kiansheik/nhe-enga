let dataset = [
    { f: "Data not loaded...", m: "circunstancial", s: "ixé", o: "xé" },
    // Add more sentences and information here
];

let currentQuestionIndex = 0;
let score = 0;
let question_count = 5;
let modes = ['indicativo', 'permissivo', 'circunstancial', 'gerundio', 'imperativo'];
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
            populateDropdown('mode', modes);
            populateDropdown('subject', ['ø', 'endé', 'ixé', 'oré', 'îandé', "pe'ẽ", "a'e"]);
            populateDropdown('object', ['ø', 'xé', 'nde', 'oré', 'îandé', "pe", "i"]);

            showQuestion();
        })
        .catch(error => {
            console.error('Error loading dataset:', error);
        });
}

function restartQuiz() {
    currentQuestionIndex = 0;
    score = 0;
    shuffleDataset();
    showQuestion();
    document.getElementById('result-container').style.display = 'none';
    document.getElementById('quiz-container').style.display = 'block';
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
    const progressFeedback = document.getElementById('progress-feedback');
    progressFeedback.innerText = `Perguntas: ${currentQuestionIndex+1}/${question_count}`;

    resetDropdowns();
    if (currentQuestionIndex < question_count) {
        const currentQuestion = dataset[currentQuestionIndex];
        document.getElementById('question').innerText = currentQuestion.f;
        partsArray = currentQuestion.d.split(' -');
        mode_val = modes.find(option => option.slice(0, 2) === currentQuestion.m)
        document.getElementById('definition').href = `${window.location.pathname}../?query=${encodeURIComponent(partsArray[0])}`
        document.getElementById('definition').innerText = partsArray[0]
        document.getElementById('definition-text').innerText = partsArray.slice(1).join(' -');
        document.getElementById('response').innerText = 'Modo: '+mode_val + '; Sujeito: ' + reverseSubjPrefMap[currentQuestion.s] + '; Objeto: ' + reverseObjPrefMap[currentQuestion.o] + ';';
    } else {
        showResult();
    }
}

function submitAnswer() {
    answers = document.querySelectorAll('.answer-container');
    answers.forEach(answer => {
        answer.style.display = 'block';
    });
    const mode = document.getElementById('mode');
    const subject = document.getElementById('subject');
    const object = document.getElementById('object');

    checkDropdownAnswer('mode', mode);
    checkDropdownAnswer('subject', subject);
    checkDropdownAnswer('object', object);

    // Move to the next question
    currentQuestionIndex++;
}

function resetDropdowns() {
    answers = document.querySelectorAll('.answer-container');
    answers.forEach(answer => {
        answer.style.display = 'none';
    });
    // Reset dropdowns to their default values
    document.getElementById('mode').value = '';
    document.getElementById('subject').value = '';
    document.getElementById('object').value = '';
    // Reset the border color of all dropdowns to default
    dropdowns = document.querySelectorAll('.option');
    dropdowns.forEach(dropdown => {
        dropdown.style.backgroundColor = '#4caf50'; // Set your default border color
    });
}

let subj_pref_map = {
    'ø': null,
    'ixé': '1ps',
    'oré': '1ppe',
    'îandé': '1ppi',
    'endé': '2ps',
    "pe'ẽ": '2pp',
    "a'e": '3p'
}
let obj_pref_map = {
    'ø': null,
    'xé': '1ps',
    'oré': '1ppe',
    'îandé': '1ppi',
    'nde': '2ps',
    "pe": '2pp',
    "i": '3p'
} 

// Function to create a reverse map
function createReverseMap(inputMap) {
    let reverseMap = {};
    for (let key in inputMap) {
        if (inputMap.hasOwnProperty(key)) {
            let value = inputMap[key];
            if (value !== null) {
                reverseMap[value] = key;
            }
        }
    }
    return reverseMap;
}

// Create reverse maps
let reverseSubjPrefMap = createReverseMap(subj_pref_map);
let reverseObjPrefMap = createReverseMap(obj_pref_map);

function checkDropdownAnswer(part, dropdownElement) {
    selectedValue = dropdownElement.value;
    const currentQuestion = dataset[currentQuestionIndex];
    is_correct = false;
    // console.log(part, selectedValue, selectedValue.substring(0, 2), currentQuestion.m)
    if (part === 'mode' && selectedValue.substring(0, 2) === currentQuestion.m) {
        score++;
        is_correct = true;
    } else if (part === 'subject' && subj_pref_map[selectedValue] === currentQuestion.s) {
        is_correct = true;
        score++;
    } else if (part === 'object' && obj_pref_map[selectedValue] === currentQuestion.o) {
        is_correct = true;
        score++;
    }
    if(!is_correct) {
        dropdownElement.style.backgroundColor = 'red';
    }
    console.log(score, currentQuestion);
}

function showResult() {
    document.getElementById('quiz-container').style.display = 'none';
    const resultContainer = document.getElementById('result-container');
    resultContainer.style.display = 'block';
    document.getElementById('score').innerText = `Your score is: ${score} out of ${question_count*3}`;
}

document.addEventListener("DOMContentLoaded", function () {
    // Your JavaScript code here
    startQuiz();
    resetDropdowns();
});