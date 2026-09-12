const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");
const results = document.getElementById("results");

const API_URL = "http://127.0.0.1:8000/search";


async function performSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        return;
    }

    searchButton.disabled = true;
    searchButton.textContent = "Searching...";

    results.innerHTML = `
        <div class="empty-state">
            Finding the most relevant conversation...
        </div>
    `;

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: query,
                top_k: 5
            })
        });

        if (!response.ok) {
            throw new Error("Search request failed");
        }

        const data = await response.json();

        renderResults(data);

    } catch (error) {

        console.error(error);

        results.innerHTML = `
            <div class="empty-state">
                Could not connect to ChatRecall API.
                <br><br>
                Make sure the FastAPI server is running.
            </div>
        `;

    } finally {

        searchButton.disabled = false;
        searchButton.textContent = "Search";
    }
}


function renderResults(data) {

    if (!data.results || data.results.length === 0) {

        results.innerHTML = `
            <div class="empty-state">
                No matching conversations found.
            </div>
        `;

        return;
    }

    const analysis = data.analysis || {};

    const intent = analysis.intent || "semantic";
    const topic = analysis.topic || "general";
    const person = analysis.person || "";
    const time = analysis.time || "";

    let metadata = `
        <div class="metadata">

            <span class="badge">
                ${capitalize(intent)}
            </span>

            ${topic !== "general" && topic !== "null"
                ? `<span class="badge">${capitalize(topic)}</span>`
                : ""
            }

            ${person
                ? `<span class="badge">${person}</span>`
                : ""
            }

            ${time
                ? `<span class="badge">${time}</span>`
                : ""
            }

        </div>
    `;

    let html = `
        <div class="results-header">

            <h2>Search results</h2>

            ${metadata}

        </div>
    `;


    data.results.forEach((result, index) => {

        const context = Array.isArray(result.context)
            ? result.context
            : [result];

        html += `
            <article class="result-card">

                <div class="result-top">

                    <div>
                        <span class="result-number">
                            #${index + 1}
                        </span>

                        <strong>${escapeHtml(result.sender)}</strong>

                        <span class="timestamp">
                            ${formatTimestamp(result.timestamp)}
                        </span>
                    </div>

                    <span class="score">
                        ${Math.round((result.score || 0) * 100)}% match
                    </span>

                </div>

                <div class="context">

                    ${context.map((message, contextIndex) => `
                        <div class="context-message ${message.id === result.id ? "target-message" : ""}">

                            <div class="message-meta">
                                <strong>${escapeHtml(message.sender)}</strong>

                                <span>
                                    ${formatTimestamp(message.timestamp)}
                                </span>
                            </div>

                            <div class="message-text">
                                ${escapeHtml(message.text)}
                            </div>

                        </div>
                    `).join("")}

                </div>

                <div class="match-info">
                    ✓ Showing ${context.length} messages of conversation context
                </div>

            </article>
        `;
    });

    results.innerHTML = html;
}


function capitalize(value) {

    if (!value) {
        return "";
    }

    return value.charAt(0).toUpperCase() + value.slice(1);
}


function formatTimestamp(timestamp) {

    if (!timestamp) {
        return "";
    }

    const date = new Date(timestamp);

    return date.toLocaleString([], {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}


function escapeHtml(value) {

    if (!value) {
        return "";
    }

    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


searchButton.addEventListener("click", performSearch);


searchInput.addEventListener("keydown", (event) => {

    if (event.key === "Enter") {
        performSearch();
    }

});


document.querySelectorAll(".examples button").forEach(button => {

    button.addEventListener("click", () => {

        searchInput.value = button.textContent.trim();

        performSearch();

    });

});