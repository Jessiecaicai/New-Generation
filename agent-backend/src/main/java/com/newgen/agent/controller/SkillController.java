package com.newgen.agent.controller;

import com.newgen.agent.service.AgentClientService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class SkillController {

    @Autowired
    private AgentClientService agentClient;

    @GetMapping("/skills")
    public Object getSkills() {
        return agentClient.getSkillsStatus();
    }

    @PutMapping("/skills/{name}/toggle")
    public void toggleSkill(@PathVariable String name,
                            @RequestParam(defaultValue = "true") boolean enabled) {
        agentClient.toggleSkill(name, enabled);
    }

    @PostMapping("/agent/reload")
    public Object reloadAgent() {
        return agentClient.reloadAgent();
    }

    @GetMapping("/prompts")
    public Object getPrompts() {
        return agentClient.getPrompts();
    }
}
