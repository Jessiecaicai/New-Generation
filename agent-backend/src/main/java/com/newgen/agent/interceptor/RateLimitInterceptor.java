package com.newgen.agent.interceptor;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 简单的滑动窗口限流拦截器。
 * 每个客户端（IP + sessionId）每分钟最多 10 次请求。
 */
@Component
public class RateLimitInterceptor implements HandlerInterceptor {

    private static final int MAX_REQUESTS_PER_MINUTE = 10;
    private static final long WINDOW_MS = 60_000L;

    private final ConcurrentHashMap<String, RateWindow> clients = new ConcurrentHashMap<>();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) throws Exception {
        // 只限流 POST /api/chat
        if (!"POST".equalsIgnoreCase(request.getMethod()) ||
            !"/api/chat".equals(request.getRequestURI())) {
            return true;
        }

        String clientKey = getClientKey(request);
        RateWindow window = clients.computeIfAbsent(clientKey, k -> new RateWindow());

        if (!window.tryAcquire()) {
            rejectRequest(response);
            return false;
        }

        return true;
    }

    private String getClientKey(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddr();
        } else {
            ip = ip.split(",")[0].trim();
        }
        // 加上 sessionId 区分同一 IP 下的不同用户
        String sessionId = request.getParameter("sessionId");
        if (sessionId == null) {
            sessionId = "anonymous";
        }
        return ip + ":" + sessionId;
    }

    private void rejectRequest(HttpServletResponse response) throws IOException {
        response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(objectMapper.writeValueAsString(
            Map.of(
                "error", "请求过于频繁，请稍后再试",
                "code", 429,
                "retryAfter", "60s"
            )
        ));
    }

    /**
     * 简单的滑动窗口计数器
     */
    private static class RateWindow {
        private final AtomicInteger count = new AtomicInteger(0);
        private volatile long windowStart = System.currentTimeMillis();

        boolean tryAcquire() {
            long now = System.currentTimeMillis();
            if (now - windowStart > WINDOW_MS) {
                // 重置窗口
                synchronized (this) {
                    if (now - windowStart > WINDOW_MS) {
                        count.set(0);
                        windowStart = now;
                    }
                }
            }
            return count.incrementAndGet() <= MAX_REQUESTS_PER_MINUTE;
        }
    }

    /**
     * 定期清理过期的客户端记录（防止内存泄漏）。
     * 由 Spring @Scheduled 调用。
     */
    public void cleanup() {
        long now = System.currentTimeMillis();
        clients.entrySet().removeIf(entry ->
            now - entry.getValue().windowStart > WINDOW_MS * 5
        );
    }
}
