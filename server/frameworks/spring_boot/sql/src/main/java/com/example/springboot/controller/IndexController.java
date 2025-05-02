package com.example.springboot.controller;

import com.example.springboot.model.SampleData;
import com.example.springboot.repository.SampleDataRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class IndexController {
    @Autowired
    private SampleDataRepository repository;

    @GetMapping("/")
    public String home() {
        StringBuilder sb = new StringBuilder();
        sb.append("<h1>Sample Data from Postgres:</h1>");
        sb.append("<ul>");

        List<SampleData> data = repository.findAll();
        for (SampleData item : data) {
            sb.append("<li>").append(item.getTitle()).append("</li>");
        }

        sb.append("</ul>");
        return sb.toString();
    }
}
