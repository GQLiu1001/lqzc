package com.lqzc;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
@MapperScan("com.lqzc.mapper")
@SpringBootApplication
public class LqzcApplication {

    public static void main(String[] args) {
        SpringApplication.run(LqzcApplication.class, args);
    }

}
