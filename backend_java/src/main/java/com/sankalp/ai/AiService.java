package com.sankalp.ai;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sankalp.ai.AiDtos.ChatTurn;

// Talks to any "OpenAI-compatible" chat API (OpenAI, NVIDIA NIM, ...): send JSON with POST, read JSON back.
// Settings (key, url, model) come from application.properties.
@Service
public class AiService {

    private final HttpClient http = HttpClient.newHttpClient();
    private final ObjectMapper json;

    @Value("${ai.api-key}")
    private String apiKey;

    @Value("${ai.base-url}")
    private String baseUrl;

    @Value("${ai.model}")
    private String defaultModel;

    public AiService(ObjectMapper json) {
        this.json = json;
    }

    public String defaultModel() {
        return defaultModel;
    }

    // Ask once, get the full answer.
    public String generate(String systemPrompt, List<ChatTurn> history, String prompt, String model,
            int maxTokens, double temperature) {
        try {
            HttpRequest request = buildRequest(systemPrompt, history, prompt, model, maxTokens, temperature, false);
            HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "AI provider error: " + response.body());
            }
            return json.readTree(response.body()).at("/choices/0/message/content").asText();
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "AI call failed: " + e.getMessage());
        }
    }

    // Ask and receive the answer piece by piece. The provider streams lines like
    //   data: {"choices":[{"delta":{"content":"Hel"}}]}
    // and we hand each piece to onToken as it arrives.
    public void stream(String systemPrompt, List<ChatTurn> history, String prompt, String model,
            int maxTokens, double temperature, Consumer<String> onToken) throws Exception {
        HttpRequest request = buildRequest(systemPrompt, history, prompt, model, maxTokens, temperature, true);
        HttpResponse<java.io.InputStream> response = http.send(request, HttpResponse.BodyHandlers.ofInputStream());
        if (response.statusCode() != 200) {
            throw new RuntimeException("AI provider error: HTTP " + response.statusCode());
        }

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(response.body()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.startsWith("data:") || line.contains("[DONE]")) {
                    continue;
                }
                String piece = json.readTree(line.substring(5)).at("/choices/0/delta/content").asText("");
                if (!piece.isEmpty()) {
                    onToken.accept(piece);
                }
            }
        }
    }

    private HttpRequest buildRequest(String systemPrompt, List<ChatTurn> history, String prompt, String model,
            int maxTokens, double temperature, boolean stream) throws Exception {
        if (apiKey.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "AI_API_KEY is not set");
        }

        // system message first, then the earlier chat, then the new question
        List<Map<String, String>> messages = new ArrayList<>();
        messages.add(Map.of("role", "system", "content", systemPrompt));
        if (history != null) {
            for (ChatTurn turn : history) {
                messages.add(Map.of("role", turn.role(), "content", turn.content()));
            }
        }
        messages.add(Map.of("role", "user", "content", prompt));

        String body = json.writeValueAsString(Map.of(
                "model", model != null ? model : defaultModel,
                "messages", messages,
                "max_tokens", maxTokens,
                "temperature", temperature,
                "stream", stream));

        return HttpRequest.newBuilder(URI.create(baseUrl + "/chat/completions"))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
    }
}
