const fs = require('fs');
const readline = require('readline');

const production_map = new Map();

function generate_output() {
    let output_string = "{\n";
    for (const entry of production_map) {
        output_string = output_string + `\t"<${entry[0]}>": [\n`;

        const tokens = entry[1].map(e => e.split(' '));
        console.log(tokens);
        let final_rule_string = "";
        for (const rule of tokens) {
            let rule_string = "";
            for (let token of rule) {
                if (production_map.has(token))
                    rule_string = rule_string + `<${token}> `;
                else
                    rule_string = rule_string + `${token} `;
            }
            rule_string = rule_string.trim();
            final_rule_string = final_rule_string + `\t\t"${rule_string}",\n`;
        }
        console.log(final_rule_string);
        console.log("----------------");

        output_string = output_string + `${final_rule_string}\t],\n`;
    }
    output_string = output_string.concat("}");

    fs.writeFile('result.json', output_string, err => {
        if (err) {
            console.error(err)
            return
        }
        console.log(output_string);
        console.log("Success");
    })
}

async function processLineByLine() {
    const fileStream = fs.createReadStream('input.ll');

    const rl = readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity
    });
    // Note: we use the crlfDelay option to recognize all instances of CR LF
    // ('\r\n') in input.ll as a single line break.

    for await (const line of rl) {
        // Each line in input.ll will be successively available here as `line`.
        try {
            const split = line.split("::=");
            const production = split[0].trim();
            const rule = split[1].trim();

            const prev_rules = production_map.get(production);
            if (prev_rules)
                production_map.set(production, [ ...prev_rules, rule ]);
            else
                production_map.set(production, [ rule ]);

        } catch (e) {
            console.error(`Failed at line ${line} with ${e}`);
        }
    }

    generate_output();
}

processLineByLine();