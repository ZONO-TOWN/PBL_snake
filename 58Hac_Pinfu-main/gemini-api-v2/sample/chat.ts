import {Chat} from "../src/geminiChat";
import * as readline from "node:readline";

const chat = new Chat();

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

async function input(question: string) : Promise<string> {
    return new Promise((resolve) => {
        rl.question(question, (answer) => {
            resolve(answer.replace("\n", ""));
        });
    });
}

async function run(){
    const question = await input('You: ');
    if (question.trim()) {
        try {
            const startTime = Date.now();
            const reply = await chat.ask(question);
            const endTime = Date.now();
            const responseTime = endTime - startTime;
            console.log("Gemini:", reply, `(${responseTime}ms)`);
            await run();
        } catch (error) {
            //console.error(`Error: ${error.message}`, 'ERROR');
        }
    }
}

run();
