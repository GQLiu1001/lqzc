package com.lqzc.controller;

import com.lqzc.ai.service.ManualImportService;
import com.lqzc.ai.service.ManualSearchService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/admin/manual")
@RequiredArgsConstructor
public class ManualController {

    private final ManualImportService manualImportService;

    @PostMapping("/import")
    public String importAll() throws Exception {
        manualImportService.importAll();
        return "OK，手册已导入 Milvus";
    }
    private final ManualSearchService manualSearchService;

    @GetMapping("/search")
    public String debugSearch(@RequestParam String q) {
        manualSearchService.testSearch(q);
        return "ok";
    }
}
