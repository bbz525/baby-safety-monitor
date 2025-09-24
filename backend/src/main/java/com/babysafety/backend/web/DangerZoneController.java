package com.babysafety.backend.web;

import com.babysafety.backend.domain.DangerZone;
import com.babysafety.backend.repository.DangerZoneRepository;
import com.babysafety.backend.web.dto.DangerZoneRequest;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/zones")
@CrossOrigin
public class DangerZoneController {

    private final DangerZoneRepository repository;

    public DangerZoneController(DangerZoneRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    @Cacheable("zones")
    public List<DangerZone> list() {
        return repository.findAll();
    }

    @PostMapping
    @CacheEvict(value = "zones", allEntries = true)
    public DangerZone create(@RequestBody DangerZoneRequest req) {
        DangerZone z = new DangerZone();
        z.setName(req.name);
        z.setPolygonJson(req.polygonJson);
        z.setLevel(req.level);
        z.setEnabled(req.enabled != null ? req.enabled : Boolean.TRUE);
        return repository.save(z);
    }

    @PutMapping("/{id}")
    @CacheEvict(value = "zones", allEntries = true)
    public DangerZone update(@PathVariable Long id, @RequestBody DangerZoneRequest req) {
        DangerZone z = repository.findById(id).orElseThrow();
        if (req.name != null) z.setName(req.name);
        if (req.polygonJson != null) z.setPolygonJson(req.polygonJson);
        if (req.level != null) z.setLevel(req.level);
        if (req.enabled != null) z.setEnabled(req.enabled);
        return repository.save(z);
    }

    @DeleteMapping("/{id}")
    @CacheEvict(value = "zones", allEntries = true)
    public void delete(@PathVariable Long id) {
        repository.deleteById(id);
    }
}


