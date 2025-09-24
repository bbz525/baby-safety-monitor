package com.babysafety.backend.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "alert",
       indexes = {
           @Index(name = "idx_alert_ts_track_zone", columnList = "ts, track_id, zone_id")
       })
public class Alert {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "ts", nullable = false)
    private Instant timestamp;

    @Column(name = "track_id")
    private String trackId;

    @Column(name = "zone_id")
    private Long zoneId;

    @Column(name = "level", nullable = false)
    private String level;

    @Column(name = "reason")
    private String reason;

    @Lob
    @Column(name = "details_json")
    private String detailsJson;

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

    public Long getZoneId() {
        return zoneId;
    }

    public void setZoneId(Long zoneId) {
        this.zoneId = zoneId;
    }

    public String getLevel() {
        return level;
    }

    public void setLevel(String level) {
        this.level = level;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }

    public String getDetailsJson() {
        return detailsJson;
    }

    public void setDetailsJson(String detailsJson) {
        this.detailsJson = detailsJson;
    }
}


