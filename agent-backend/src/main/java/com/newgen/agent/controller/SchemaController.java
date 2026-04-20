package com.newgen.agent.controller;

import com.newgen.agent.model.dto.SchemaMetadataDto;
import com.newgen.agent.service.SchemaService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/schema")
public class SchemaController {

    @Autowired
    private SchemaService schemaService;

    @GetMapping
    public SchemaMetadataDto getSchema() {
        return schemaService.getFullSchema();
    }

    @PostMapping("/refresh")
    public void refresh() {
        schemaService.invalidateCache();
    }
}
