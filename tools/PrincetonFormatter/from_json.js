const fs = require('fs');
const crypto = require('crypto');

const production_map = new Map();

function formatEntry(entry) {
    if (entry === "")
        return "\'\'";
    if (entry === " ")
        return "s";

    return entry.replaceAll(/<[^>]*>/g, function(match, group) {
        return ` ${generateKey(match)} `;
    });
}

function generateKey(value) {
    const hash = crypto.createHash('sha256').update(value).digest('hex');
    return `KEY_${value.replace(/[^a-z0-9]/gi, '')}_${hash.substr(0, 8)}`;
}

function generateOutput(content) {
    let output = "";
    for (let key in content) {
        if (!content.hasOwnProperty(key)) {
            throw Error(`hasOwnProperty error for key: ${key}`);
        }
        for (let entry of content[key]) {
            output += `${generateKey(key)} ::= ${formatEntry(entry)}\n`;
        }
    }

    fs.writeFile('result.ll', output, err => {
        if (err) {
            console.error(err)
            return
        }
        console.log(output);
        console.log("Success");
    })
}

function processFile() {
    const contentRaw = fs.readFileSync('input.json');
    const content = JSON.parse(contentRaw.toString());
    generateOutput(content);
}

processFile();