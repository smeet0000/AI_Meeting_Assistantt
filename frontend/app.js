const API = "http://127.0.0.1:8000";

const btn = document.getElementById("analyzeBtn");
const fileInput = document.getElementById("videoFile");

alert("JS Loaded");

btn.addEventListener("click", async function (event) {

    // Prevent page reload / default browser action
    event.preventDefault();

    alert("1. Button Clicked");

    const file = fileInput.files[0];

    if (!file) {
        alert("No File Selected");
        return;
    }

    alert("2. File Selected: " + file.name);

    const formData = new FormData();

    formData.append("file", file);
    formData.append("language", "english");

    alert("3. FormData Created");

    try {

        alert("4. Before Fetch");

        const response = await fetch(
            `${API}/analyze/file`,
            {
                method: "POST",
                body: formData
            }
        );

        alert("5. After Fetch");

        console.log("Response status:", response.status);

        alert(
            "Status = " + response.status
        );

        const text = await response.text();

        alert("6. Response Received");

        console.log(
            "Raw backend response:",
            text
        );

        if (!response.ok) {

            throw new Error(
                `Backend returned ${response.status}: ${text}`
            );
        }

        const result = JSON.parse(text);

        alert("7. JSON Parsed");

        console.log(
            "Parsed result:",
            result
        );

        // -----------------------------
        // Display title
        // -----------------------------

        document.getElementById("title").innerText =
            result.title || "No title";

        alert("8. Title Done");


        // -----------------------------
        // Display summary
        // -----------------------------

        document.getElementById("summary").innerText =
            result.summary || "No summary";

        alert("9. Summary Done");


        // -----------------------------
        // Display action items
        // -----------------------------

        document.getElementById("actionItems").innerText =
            result.action_items || "No action items";

        alert("10. Action Items Done");


        // -----------------------------
        // Display key decisions
        // -----------------------------

        document.getElementById("keyDecisions").innerText =
            result.key_decisions || "No key decisions";

        alert("11. Key Decisions Done");


        // -----------------------------
        // Display open questions
        // -----------------------------

        document.getElementById("openQuestions").innerText =
            result.open_questions || "No open questions";

        alert("12. Open Questions Done");


        // -----------------------------
        // Display transcript
        // -----------------------------

        document.getElementById("transcript").value =
            result.transcript || "";

        alert("13. Transcript Done");

    } catch (error) {

        console.error(
            "Frontend error:",
            error
        );

        alert(
            "ERROR: " + error.message
        );
    }
});