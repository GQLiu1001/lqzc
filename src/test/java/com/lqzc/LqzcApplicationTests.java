package com.lqzc;

import com.lqzc.utils.YearMonthUtil;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

@SpringBootTest
class LqzcApplicationTests {

    @Test
    void contextLoads() {
        List<String> format = YearMonthUtil.format(2025, 12, 12);
        System.out.println(format);
    }

}
