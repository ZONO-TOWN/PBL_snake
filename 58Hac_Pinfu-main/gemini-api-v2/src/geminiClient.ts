import { GoogleGenerativeAI } from "@google/generative-ai";
import { config } from "./config";

export const genAI = new GoogleGenerativeAI(config.geminiApiKey);
