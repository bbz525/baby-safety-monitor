package com.babysafety.backend.repository;

import com.babysafety.backend.domain.Alert;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AlertRepository extends JpaRepository<Alert, Long> {
}


