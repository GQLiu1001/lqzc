package com.lqzc.utils;

import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

public class YearMonthUtil {
    public static List<String> format (Integer year , Integer month , Integer length) {
//        List<String> list = new ArrayList<String>();
//        String yearMonth = "";
//        if (month > length) {
//            for (int i = length; i > 0; i--) {
//                if (month < 10 && month > 0) {
//                    String monthStr = "-0" + month;
//                    yearMonth = year + monthStr;
//                    list.add(yearMonth);
//                    month--;
//                } else {
//                    String monthStr = "-" + month;
//                    yearMonth = year + monthStr;
//                    list.add(yearMonth);
//                    month--;
//                }
//            }
//        } else {
//            Integer m = month;
//            for (int i = month; i > 0; i--) {
//                String monthStr = "-0" + month;
//                yearMonth = year + monthStr;
//                list.add(yearMonth);
//                month--;
//            }
//            int num = length - m;
//            for (int n = 0; n <= num / 12 + 1; n++) {
//                if (n>=1){
//                    num = num - 12;
//                }
//                year = year - 1;
//                for (int i = 12; i > 12 - num && i>0; i--) {
//                    if (i < 10) {
//                        String monthStr = "-0" + i;
//                        yearMonth = year + monthStr;
//                        list.add(yearMonth);
//                    } else {
//                        String monthStr = "-" + i;
//                        yearMonth = year + monthStr;
//                        list.add(yearMonth);
//                    }
//                }
//            }
//        }
//        return list;
//    }
        List<String> list = new ArrayList<>();
        if (length <= 0) {
            return list;
        }

        YearMonth ym = YearMonth.of(year, month);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM");

        for (int i = 0; i < length; i++) {
            list.add(ym.minusMonths(i).format(formatter));
        }

        return list;
    }
}
