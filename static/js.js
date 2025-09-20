
// ******************************************************************************************
// GPT

function generateTextByGPT() {
    // Smazáni obsahu
    document.getElementById("generatedText").value = "";
    document.getElementById("usedModel").value = "";
    document.getElementById("inputTokens").value = "";
    document.getElementById("outputTokens").value = "";
    
    // Vstupy pro GPT
    configGPT = document.getElementById("configAI").value;
    textForGPT = document.getElementById("exportedText").value;
    gptModel = document.getElementById("gpt_model").value;


    // Odeslání požadavku na server
    fetch('/reviewhub/gpt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin',              // ← DŮLEŽITÉ
        body: JSON.stringify({ configGPT, textForGPT, gptModel })
    })
    .then(response => response.json())
    .then(data => {
        // Zobrazení výstupů GPT
        document.getElementById("generatedText").value = data.generatedText;
        document.getElementById("usedModel").value = data.model_used;
        document.getElementById("inputTokens").value = data.input_tokens;
        document.getElementById("outputTokens").value = data.output_tokens;
    })
    .catch(error => console.error('Chyba při ukládání:', error));
}

function exportPaperToStructureByGPT() {
    // Smazáni obsahu
    document.getElementById("generatedText").value = "";    
    
    // Vstupy pro GPT
    
    gptModel = document.getElementById("gpt_model").value;
    configGPT = document.getElementById("configAI").value;
    textForGPT = document.getElementById("extractedText").value;

    // Odeslání požadavku na server
    fetch('/reviewhub/gpt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
	credentials: 'same-origin',
        body: JSON.stringify({ configGPT, textForGPT, gptModel })
    })
    .then(response => response.json())
    .then(data => {
        // Zobrazení výstupů GPT
        document.getElementById("generatedText").value = data.generatedText;
        document.getElementById("usedModel").value = data.model_used;
        document.getElementById("inputTokens").value = data.input_tokens;
        document.getElementById("outputTokens").value = data.output_tokens;
    })
    .catch(error => console.error('Chyba při ukládání:', error));
}

// ******************************************************************************************
// MODALNI OKNO
// Obsluha modalnho okna pro potvrzeni smazani clanku, rpojektu, uzivatele apod.
let deleteUrl = '';

function openDeleteModal(url, name) {

    deleteUrl = url;
    document.getElementById('delete-modal').style.display = 'block';
    document.getElementById('delete-modalContent-name').innerHTML = name
}

function closeModal() {
    document.getElementById('delete-modal').style.display = 'none';
}

function confirmDeletion() {
    window.location.href = deleteUrl;
}


function parseSections(input) {
    const lines = input.trim().split("\n");
    const jsonOutput = { sections: [] };
    const sectionStack = [jsonOutput.sections];

    lines.forEach(line => {
        const trimmed = line.replace(/\t/g, ' ').trim();
        const [section, ...titleParts] = trimmed.split(" ");
        const title = titleParts.join(" ");
        const level = section.split('.').length - 1;

        const sectionObj = title.includes(" ") ? { [`${section} ${title}`]: [] } : `${section} ${title}`;

        // Ensure stack depth corresponds to the section level
        while (sectionStack.length > level + 1) {
            sectionStack.pop();
        }

        const currentLevel = sectionStack[sectionStack.length - 1];

        if (typeof sectionObj === "string") {
            currentLevel.push(sectionObj);
        } else {
            currentLevel.push(sectionObj);
            sectionStack.push(sectionObj[`${section} ${title}`]);
        }
    });

    return jsonOutput;
}


// ******************************************************************************************
// Stažení textu z textarea jako txt soubor
// id_textarea      ID textarea ze ktereho se ma stahnout obsah v txt souboru
function downloadTextFromTextarea(id_textarea) {
    // Získání textu z textarea
    const text = document.getElementById(id_textarea).value;
    
    // Vytvoření Blob objektu pro obsah souboru
    const blob = new Blob([text], { type: "text/plain" });
    
    // Vytvoření URL pro Blob objekt
    const url = URL.createObjectURL(blob);
    
    // Vytvoření dočasného odkazu pro stažení
    const a = document.createElement("a");
    a.href = url;
    a.download = "export.txt";  // Název souboru, který bude stažen
    
    // Automatické kliknutí na odkaz ke stažení a následné odstranění odkazu
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    // Uvolnění URL
    URL.revokeObjectURL(url);
}


