package com.babysafety.backend.repository;

import com.babysafety.backend.domain.VisionEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.Instant;
import java.util.List;

public interface VisionEventRepository extends JpaRepository<VisionEvent, Long> {

    @Query("select v from VisionEvent v where v.timestamp >= :since order by v.timestamp desc")
    List<VisionEvent> findRecentSince(@Param("since") Instant since);
}


