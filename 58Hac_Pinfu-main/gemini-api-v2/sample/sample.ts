import {Chat} from "../src/geminiChat";

const chat = new Chat();

(async () => {
    const reply = await chat.ask("こんにちは");
    console.log("Gemini:", reply);

    chat.resetSession(); // セッションをリセット
})();