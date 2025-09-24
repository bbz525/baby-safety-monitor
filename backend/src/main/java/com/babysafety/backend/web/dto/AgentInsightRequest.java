package com.babysafety.backend.web.dto;

public class AgentInsightRequest {
    public String timestamp; // ISO-8601
    public String trackId;
    public Long zoneId;
    public String level; // info/warn/critical
    public String reason;
    public String detailsJson;
}


