const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");
const results = document.getElementById("results");

searchButton.addEventListener("click", () => {
    const query = searchInput.value.trim();

    if (!query) {
        return;
    }

    results.innerHTML = `
        <div class="empty-state">
            Search engine coming in Phase 2...
        </div>
    `;
});


document.querySelectorAll(".examples button").forEach(button => {

    button.addEventListener("click", () => {

        searchInput.value = button.textContent;

        searchInput.focus();

    });

});