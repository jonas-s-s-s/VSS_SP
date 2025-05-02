package com.example.springboot.repository;

import com.example.springboot.model.SampleData;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SampleDataRepository extends JpaRepository<SampleData, Long> {
}
