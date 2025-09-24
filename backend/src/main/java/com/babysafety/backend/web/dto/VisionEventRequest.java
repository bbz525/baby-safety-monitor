package com.babysafety.backend.web.dto;

public class VisionEventRequest {
    public String timestamp; // ISO-8601
    public String trackId;
    public int[] bbox; // [x,y,w,h]
    public String action;
    public Double riskScore;
}


