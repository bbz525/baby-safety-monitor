package com.babysafety.backend.web;

import com.babysafety.backend.domain.VisionEvent;
import com.babysafety.backend.repository.VisionEventRepository;
import com.babysafety.backend.service.SseHub;
import com.babysafety.backend.web.dto.VisionEventRequest;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.time.Instant;
import java.time.Duration;
import java.time.format.DateTimeParseException;
import java.util.List;

@RestController
@RequestMapping("/api/events")
@CrossOrigin
public class VisionEventController {

    private final VisionEventRepository repository;
    private final SseHub sseHub;

    public VisionEventController(VisionEventRepository repository, SseHub sseHub) {
        this.repository = repository;
        this.sseHub = sseHub;
    }

    @PostMapping("/vision")
    public void receiveVisionEvent(@RequestBody VisionEventRequest req) {
        VisionEvent v = new VisionEvent();
        Instant ts = parseTimestamp(req.timestamp);
        v.setTimestamp(ts != null ? ts : Instant.now());
        v.setTrackId(req.trackId);
        if (req.bbox != null && req.bbox.length == 4) {
            v.setX(req.bbox[0]);
            v.setY(req.bbox[1]);
            v.setW(req.bbox[2]);
            v.setH(req.bbox[3]);
        }
        v.setAction(req.action);
        v.setRiskScore(req.riskScore);
        VisionEvent saved = repository.save(v);
        sseHub.send(saved);
    }

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        return sseHub.subscribe(0L);
    }

    @GetMapping("/recent")
    public List<VisionEvent> recent(@RequestParam(name = "minutes", defaultValue = "10") int minutes) {
        Instant since = Instant.now().minus(Duration.ofMinutes(minutes));
        return repository.findRecentSince(since);
    }

    private Instant parseTimestamp(String s) {
        if (s == null || s.isEmpty()) return null;
        try {
            return Instant.parse(s);
        } catch (DateTimeParseException e) {
            return null;
        }
    }
}


