/**
 * Chatbot Configuration
 *
 * Centralized configuration for the AI chatbot component, pulled from .env variables.
 */

// Free tier settings
export const FREE_QUESTIONS_LIMIT = import.meta.env.CHATBOT_FREE_QUESTIONS_LIMIT || 10;

// Warning threshold (when to show "running out" warning)
// Set to FREE_QUESTIONS_LIMIT - 2 by default (warns when 2 questions left)
export const FREE_QUESTIONS_WARNING_THRESHOLD = import.meta.env.CHATBOT_FREE_QUESTIONS_WARNING_THRESHOLD;

// API configuration
export const CHATBOT_API_URL = import.meta.env.PUBLIC_CHATBOT_API_URL;

// UI settings
export const CHATBOT_EXPANDED_WIDTH = import.meta.env.CHATBOT_EXPANDED_WIDTH;
export const CHATBOT_COMPACT_WIDTH = import.meta.env.CHATBOT_COMPACT_WIDTH;

// Response settings
export const CHATBOT_MODEL = import.meta.env.CHATBOT_MODEL;
export const CHATBOT_TEMPERATURE = import.meta.env.CHATBOT_TEMPERATURE;
export const CHATBOT_MAX_TOKENS = import.meta.env.CHATBOT_MAX_TOKENS;
