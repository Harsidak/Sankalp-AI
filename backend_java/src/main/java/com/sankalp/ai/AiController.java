package com.sankalp.ai;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import com.sankalp.ai.AiDtos.InferenceRequest;
import com.sankalp.ai.AiDtos.InferenceResponse;
import com.sankalp.ai.AiDtos.ModelInfo;
import com.sankalp.ai.AiDtos.ReflectionRequest;
import com.sankalp.ai.AiDtos.ReflectionResponse;
import com.sankalp.common.ApiResponse;

@RestController
@RequestMapping("/api/v1/ai")
public class AiController {

    // The companion's personality and safety rules live on the server so the browser cannot change them.
    private static final String COMPANION_PROMPT = "You are SanKalp, a wellness companion inside a mood-and-habit "
            + "journalling app. Be warm, concrete and brief -- usually under 120 words. Reflect what the person is "
            + "feeling before offering anything. Suggest at most one small next step, and only when it is wanted.\n"
            + "You are not a clinician: never diagnose, never discuss medication, and never present yourself as "
            + "therapy. If someone describes self-harm, abuse, or a crisis, say plainly that this is beyond what you "
            + "can help with and encourage them to contact a local crisis line or someone they trust.";

    private static final Map<String, String> TONES = Map.of(
            "supportive", "You are a warm, grounded wellness companion. Reflect back what the person seems to be "
                    + "feeling in two or three sentences. Do not give medical advice, do not diagnose, and do not be saccharine.",
            "practical", "You are a calm, practical wellness companion. In two or three sentences, name what the "
                    + "person is dealing with and suggest one small, concrete next step. Do not give medical advice.",
            "curious", "You are a thoughtful wellness companion. In two or three sentences, reflect what you notice "
                    + "and ask one open question that helps the person think further. Do not give medical advice.");

    private final AiService ai;

    public AiController(AiService ai) {
        this.ai = ai;
    }

    // Full answer in one go
    @PostMapping("/inference")
    public ApiResponse<InferenceResponse> inference(@RequestBody InferenceRequest req) {
        String model = req.model() != null ? req.model() : ai.defaultModel();
        String answer = ai.generate(systemPromptOf(req), req.history(), req.prompt(), model,
                req.maxTokens() != null ? req.maxTokens() : 1024,
                req.temperature() != null ? req.temperature() : 0.7);
        return ApiResponse.ok(new InferenceResponse(answer, model, "openai-compatible"));
    }

    // Answer streamed word by word with Server-Sent Events (SSE): the connection stays open
    // and the server keeps pushing "data: {...}" lines. The React chat reads them as they arrive.
    @PostMapping("/stream")
    public SseEmitter stream(@RequestBody InferenceRequest req) {
        SseEmitter emitter = new SseEmitter(0L); // 0 = no timeout

        // Run in another thread so this method can return the emitter immediately.
        CompletableFuture.runAsync(() -> {
            try {
                ai.stream(systemPromptOf(req), req.history(), req.prompt(), req.model(),
                        req.maxTokens() != null ? req.maxTokens() : 1024,
                        req.temperature() != null ? req.temperature() : 0.7,
                        token -> send(emitter, Map.of("content", token, "done", false)));
                send(emitter, Map.of("content", "", "done", true));
                emitter.complete();
            } catch (Exception e) {
                send(emitter, Map.of("error", String.valueOf(e.getMessage())));
                emitter.complete();
            }
        });
        return emitter;
    }

    // A short reflection on something the user wrote (journal entry, check-in note)
    @PostMapping("/reflect")
    public ApiResponse<ReflectionResponse> reflect(@RequestBody ReflectionRequest req) {
        String system = TONES.getOrDefault(req.tone(), TONES.get("supportive"));
        String answer = ai.generate(system, null, req.text(), null, 300, 0.8);
        return ApiResponse.ok(new ReflectionResponse(answer, ai.defaultModel(), "openai-compatible"));
    }

    @GetMapping("/models")
    public ApiResponse<List<ModelInfo>> models() {
        return ApiResponse.ok(List.of(
                new ModelInfo(ai.defaultModel(), "openai-compatible", "Default model", 8192, true, true)));
    }

    private String systemPromptOf(InferenceRequest req) {
        return req.systemPrompt() != null ? req.systemPrompt() : COMPANION_PROMPT;
    }

    private void send(SseEmitter emitter, Map<String, Object> data) {
        try {
            emitter.send(SseEmitter.event().name("token").data(data));
        } catch (Exception e) {
            throw new RuntimeException(e); // the browser closed the connection: stop streaming
        }
    }
}
