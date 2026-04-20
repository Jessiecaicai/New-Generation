package com.newgen.agent.service;

import com.newgen.agent.exception.AgentServiceException;
import com.newgen.agent.model.dto.AgentRequestDto;
import com.newgen.agent.model.dto.AgentResponseDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Slf4j
@Service
public class AgentClientService {

    @Autowired
    private RestTemplate restTemplate;

    @Value("${agent.service.url:http://localhost:8001}")
    private String agentServiceUrl;

    public AgentResponseDto sendChatRequest(AgentRequestDto request) {
        String url = agentServiceUrl + "/chat";
        log.info("Calling Python agent: {}", url);

        try {
            AgentResponseDto response = restTemplate.postForObject(url, request, AgentResponseDto.class);
            if (response == null) {
                throw new AgentServiceException("Agent 返回空响应");
            }
            log.info("Agent response intent: {}", response.getIntent());
            return response;
        } catch (AgentServiceException e) {
            throw e;
        } catch (Exception e) {
            log.error("Agent service call failed: {}", e.getMessage());
            throw new AgentServiceException("调用 Agent 服务失败: " + e.getMessage());
        }
    }

    public Object getSkillsStatus() {
        return restTemplate.getForObject(agentServiceUrl + "/skills/status", Object.class);
    }

    public void toggleSkill(String name, boolean enabled) {
        restTemplate.put(agentServiceUrl + "/skills/" + name + "/toggle?enabled=" + enabled, null);
    }

    public Object reloadAgent() {
        return restTemplate.postForObject(agentServiceUrl + "/skills/reload", null, Object.class);
    }

    public Object getPrompts() {
        return restTemplate.getForObject(agentServiceUrl + "/skills/prompts", Object.class);
    }
}
