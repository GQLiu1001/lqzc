package com.lqzc;

import com.lqzc.utils.YearMonthUtil;
import org.junit.jupiter.api.Test;

import java.util.List;

class LqzcApplicationTests {

    @Test
    void contextLoads() {
        List<String> format = YearMonthUtil.format(2025, 12, 12);
        System.out.println(format);
    }

}
