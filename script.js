// User review showing certain ammount of text length at index page
document.getElementById("comment").innerText = truncateText();

function truncateText() {
    let element = document.getElementById("comment");
    let text = element.innerText;
    const textMaxLength = 55;


    if (text.length > textMaxLength) {
        let truncated = text.substr(0, textMaxLength) + "..."
    }

    return truncated
}