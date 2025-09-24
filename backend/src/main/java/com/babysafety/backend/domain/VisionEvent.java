package com.babysafety.backend.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "vision_event",
       indexes = {
           @Index(name = "idx_vision_event_ts_track", columnList = "ts, track_id")
       })
public class VisionEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "ts", nullable = false)
    private Instant timestamp;

    @Column(name = "track_id", nullable = false)
    private String trackId;

    @Column(name = "x", nullable = false)
    private Integer x;

    @Column(name = "y", nullable = false)
    private Integer y;

    @Column(name = "w", nullable = false)
    private Integer w;

    @Column(name = "h", nullable = false)
    private Integer h;

    @Column(name = "action")
    private String action;

    @Column(name = "risk_score")
    private Double riskScore;

    public Long getId() {
        return id;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    public String getTrackId() {
        return trackId;
    }

    public void setTrackId(String trackId) {
        this.trackId = trackId;
    }

    public Integer getX() {
        return x;
    }

    public void setX(Integer x) {
        this.x = x;
    }

    public Integer getY() {
        return y;
    }

    public void setY(Integer y) {
        this.y = y;
    }

    public Integer getW() {
        return w;
    }

    public void setW(Integer w) {
        this.w = w;
    }

    public Integer getH() {
        return h;
    }

    public void setH(Integer h) {
        this.h = h;
    }

    public String getAction() {
        return action;
    }

    public void setAction(String action) {
        this.action = action;
    }

    public Double getRiskScore() {
        return riskScore;
    }

    public void setRiskScore(Double riskScore) {
        this.riskScore = riskScore;
    }
}


