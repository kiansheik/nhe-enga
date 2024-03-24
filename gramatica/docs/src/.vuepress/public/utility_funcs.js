function swapTitleAndInnerText(event) {
    const spanElement = event.target.closest('span');
const oldTitle = spanElement.getAttribute('title');
const oldInnerText = spanElement.innerText;
spanElement.setAttribute('title', oldInnerText);
spanElement.innerText = oldTitle;
}
