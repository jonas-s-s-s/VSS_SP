package com.example.springboot.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.Random;

@RestController
public class IndexController {

    private final ObjectMapper mapper = new ObjectMapper();
    private final Random random = new Random();

    @GetMapping(value = "/", produces = MediaType.TEXT_HTML_VALUE)
    public String home() throws JsonProcessingException {
        ObjectNode obj = mapper.createObjectNode();
        obj.put("message", "Hello World");
        obj.put("timestamp", Instant.now().toString());
        obj.put("randomNumber", random.nextInt(1000));

        String prettyJson = mapper.writerWithDefaultPrettyPrinter()
                                  .writeValueAsString(obj);

        return "<!DOCTYPE html>"
             + "<html><head><meta charset=\"UTF-8\"><title>Hello JSON</title></head>"
             + "<body><pre>" + prettyJson + "</pre></body></html>";
    }
}
