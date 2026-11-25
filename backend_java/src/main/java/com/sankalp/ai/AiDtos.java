package com.sankalp.ai;

import java.util.List;

public class AiDtos {

    // role is "user" or "assistant"
    public record ChatTurn(String role, String content) {
    }

    // Everything except prompt is optional. history = earlier messages of the chat (the API remembers nothing).
    public record InferenceRequest(String prompt, List<ChatTurn> history, String systemPrompt, String model,
            Integer maxTokens, Double temperature) {
    }

    public record InferenceResponse(String content, String model, String provider) {
    }

    // tone: supportive | practical | curious
    public record ReflectionRequest(String text, String tone) {
    }

    public record ReflectionResponse(String reflection, String model, String provider) {
    }

    public record ModelInfo(String name, String provider, String description, int maxTokens,
            boolean supportsStreaming, boolean isDefault) {
    }
}
