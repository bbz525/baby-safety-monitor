package com.babysafety.backend.service;

import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@Component
public class SseHub {
    private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();

    public SseEmitter subscribe(long timeoutMillis) {
        SseEmitter emitter = new SseEmitter(timeoutMillis);
        emitters.add(emitter);
        emitter.onCompletion(() -> emitters.remove(emitter));
        emitter.onTimeout(() -> emitters.remove(emitter));
        return emitter;
    }

    public void send(Object data) {
        for (SseEmitter emitter : emitters) {
            try {
                emitter.send(SseEmitter.event().name("event").data(data));
            } catch (IOException e) {
                emitter.complete();
                emitters.remove(emitter);
            }
        }
    }
}


