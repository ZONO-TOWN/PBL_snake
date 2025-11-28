import { genAI } from "./geminiClient";
import { config } from "./config";

export class Chat {
    private chatSession: ReturnType<typeof this.model.startChat>;
    private model = genAI.getGenerativeModel({ model: config.model });

    constructor() {
        this.chatSession = this.model.startChat();
    }

    async ask(userMessage: string): Promise<string> {
        const result = await this.chatSession.sendMessage(userMessage);
        return result.response.text();
    }

    resetSession() {
        this.chatSession = this.model.startChat();
    }
}