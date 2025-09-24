package com.babysafety.backend.web;

import com.babysafety.backend.domain.Alert;
import com.babysafety.backend.repository.AlertRepository;
import com.babysafety.backend.service.SseHub;
import com.babysafety.backend.service.NotifierService;
import com.babysafety.backend.web.dto.AgentInsightRequest;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.time.format.DateTimeParseException;

@RestController
@RequestMapping("/api/agent")
@CrossOrigin
public class AgentController {

    private final AlertRepository alertRepository;
    private final SseHub sseHub;
    private final NotifierService notifierService;

    public AgentController(AlertRepository alertRepository, SseHub sseHub, NotifierService notifierService) {
        this.alertRepository = alertRepository;
        this.sseHub = sseHub;
        this.notifierService = notifierService;
    }

    @PostMapping("/insights")
    public Alert receiveInsight(@RequestBody AgentInsightRequest req) {
        Alert a = new Alert();
        a.setTimestamp(parse(req.timestamp));
        a.setTrackId(req.trackId);
        a.setZoneId(req.zoneId);
        a.setLevel(req.level);
        a.setReason(req.reason);
        a.setDetailsJson(req.detailsJson);
        Alert saved = alertRepository.save(a);
        sseHub.send(saved);
        notifierService.notifyAlert(saved);
        return saved;
    }

    private Instant parse(String s) {
        if (s == null || s.isEmpty()) return Instant.now();
        try { return Instant.parse(s); } catch (DateTimeParseException e) { return Instant.now(); }
    }
}


