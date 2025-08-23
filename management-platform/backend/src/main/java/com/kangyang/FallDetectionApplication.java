package com.kangyang;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableAsync
@EnableScheduling
public class FallDetectionApplication {
    public static void main(String[] args) {
        SpringApplication.run(FallDetectionApplication.class, args);
        System.out.println("康养跌倒检测后端服务启动成功！");
    }
}