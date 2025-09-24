package com.babysafety.backend.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "danger_zone",
       uniqueConstraints = {
           @UniqueConstraint(name = "uk_zone_name", columnNames = {"name"})
       })
public class DangerZone {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "name", nullable = false)
    private String name;

    @Lob
    @Column(name = "polygon_json", nullable = false)
    private String polygonJson;

    @Column(name = "level", nullable = false)
    private String level;

    @Column(name = "enabled", nullable = false)
    private Boolean enabled = true;

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getPolygonJson() {
        return polygonJson;
    }

    public void setPolygonJson(String polygonJson) {
        this.polygonJson = polygonJson;
    }

    public String getLevel() {
        return level;
    }

    public void setLevel(String level) {
        this.level = level;
    }

    public Boolean getEnabled() {
        return enabled;
    }

    public void setEnabled(Boolean enabled) {
        this.enabled = enabled;
    }
}


