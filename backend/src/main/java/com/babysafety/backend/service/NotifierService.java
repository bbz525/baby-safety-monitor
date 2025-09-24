package com.babysafety.backend.service;

import com.babysafety.backend.domain.Alert;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.format.DateTimeFormatter;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

@Component
public class NotifierService {

    @Value("${app.notify.dingtalk.webhook:}")
    private String dingtalkWebhook;

    @Value("${app.notify.dingtalk.secret:}")
    private String dingtalkSecret;

    private final HttpClient httpClient = HttpClient.newHttpClient();

    public void notifyAlert(Alert alert) {
        if (dingtalkWebhook == null || dingtalkWebhook.isBlank()) return;
        try {
            String webhook = signIfNeeded(dingtalkWebhook, dingtalkSecret);
            String content = buildContent(alert);
            String body = "{\n" +
                    "  \"msgtype\": \"text\",\n" +
                    "  \"text\": { \"content\": " + jsonEscape(content) + " }\n" +
                    "}";

            HttpRequest req = HttpRequest.newBuilder(URI.create(webhook))
                    .header("Content-Type", "application/json;charset=utf-8")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();
            httpClient.sendAsync(req, HttpResponse.BodyHandlers.discarding());
        } catch (Exception ignored) {
        }
    }

    private String buildContent(Alert a) {
        String ts = a.getTimestamp() != null ? DateTimeFormatter.ISO_INSTANT.format(a.getTimestamp()) : "";
        String reason = a.getReason() != null ? a.getReason() : "";
        String level = a.getLevel() != null ? a.getLevel() : "";
        String track = a.getTrackId() != null ? a.getTrackId() : "";
        return String.format("[告警]%s 级别:%s 轨迹:%s 原因:%s", ts, level, track, reason);
    }

    private String jsonEscape(String s) {
        String escaped = s
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n");
        return "\"" + escaped + "\"";
    }

    private String signIfNeeded(String webhook, String secret) {
        if (secret == null || secret.isBlank()) return webhook;
        long timestamp = System.currentTimeMillis();
        try {
            String stringToSign = timestamp + "\n" + secret;
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            byte[] signData = mac.doFinal(stringToSign.getBytes(StandardCharsets.UTF_8));
            String sign = URLEncoder.encode(Base64.getEncoder().encodeToString(signData), StandardCharsets.UTF_8);
            String sep = webhook.contains("?") ? "&" : "?";
            return webhook + sep + "timestamp=" + timestamp + "&sign=" + sign;
        } catch (Exception e) {
            return webhook;
        }
    }
}


