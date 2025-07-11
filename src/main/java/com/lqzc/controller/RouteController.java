package com.lqzc.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.lqzc.common.Result;
import com.lqzc.common.resp.RouteResp;
import com.lqzc.utils.UserContextHolder;
import com.lqzc.common.props.WxConfigProperties;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Tag(name = "派送系统路线规划相关接口")
@RestController
public class RouteController {

    @Resource
    private WxConfigProperties wxConfigProperties;

    @Value("${tencent.map.key}")
    private String tencentMapKey;


    @Resource
    private RestTemplate restTemplate;
    /**
     * 腾讯地图路线规划
     */
    @Operation(summary = "腾讯地图路线规划", description = "基于腾讯地图API进行路线规划")
    @GetMapping("/route")
    public Result<RouteResp> route(@Parameter(description = "起点纬度", required = true) @RequestParam BigDecimal fromLat,
                          @Parameter(description = "终点纬度", required = true) @RequestParam BigDecimal toLat,
                          @Parameter(description = "起点经度", required = true) @RequestParam BigDecimal fromLng,
                          @Parameter(description = "终点经度", required = true) @RequestParam BigDecimal toLng) {
        System.out.println("当前线程: " + Thread.currentThread().getName());
        System.out.println("司机"+ UserContextHolder.getUserId()+"触发腾讯地图路线规划");
        System.out.println("去向 = " + "toLat" + toLat + ",toLng" + toLng);
        // 校验经纬度范围
        if (fromLat.compareTo(BigDecimal.valueOf(-90)) < 0 || fromLat.compareTo(BigDecimal.valueOf(90)) > 0 ||
                fromLng.compareTo(BigDecimal.valueOf(-180)) < 0 || fromLng.compareTo(BigDecimal.valueOf(180)) > 0 ||
                toLat.compareTo(BigDecimal.valueOf(-90)) < 0 || toLat.compareTo(BigDecimal.valueOf(90)) > 0 ||
                toLng.compareTo(BigDecimal.valueOf(-180)) < 0 || toLng.compareTo(BigDecimal.valueOf(180)) > 0) {
            throw new IllegalArgumentException("经纬度超出有效范围");
        }

        // 使用 UriComponentsBuilder 构造 URL
        String from = fromLat + "," + fromLng;
        String to = toLat + "," + toLng;
        String url = UriComponentsBuilder.fromUriString(wxConfigProperties.getTencentMapApi())
                .queryParam("from", from)
                .queryParam("to", to)
                .queryParam("key", tencentMapKey)
                // .queryParam("policy", "0") // 暂时移除 policy 参数，测试默认值
                .build()
                .toUriString();
        try {
            // 调用腾讯地图 API
            String response = restTemplate.getForObject(url, String.class);

            // 解析 JSON 响应
            ObjectMapper mapper = new ObjectMapper();
            JsonNode root = mapper.readTree(response);

            // 检查请求状态
            if (root.get("status").asInt() != 0) {
                throw new RuntimeException("腾讯地图 API 请求失败: " + root.get("message").asText());
            }

            // 提取第一条路线信息（routes[0]）
            JsonNode routeNode = root.get("result").get("routes").get(0);
            RouteResp routeResp = new RouteResp();
            routeResp.setDistance(routeNode.get("distance").asInt());
            routeResp.setDuration(routeNode.get("duration").asInt());

            // 提取第一条路线的完整 polyline
            JsonNode polylineNode = routeNode.get("polyline");
            List<List<BigDecimal>> polyline = new ArrayList<>();
            BigDecimal lastLat = null;
            BigDecimal lastLng = null;

            for (int i = 0; i < polylineNode.size(); i += 2) {
                BigDecimal lat, lng;

                if (i == 0) {
                    // 第一个点是绝对坐标 [纬度,经度]
                    lat = new BigDecimal(polylineNode.get(i).asText());
                    lng = new BigDecimal(polylineNode.get(i + 1).asText());
                } else {
                    // 后续点是差值，需要计算出绝对坐标
                    BigDecimal latDiff = new BigDecimal(polylineNode.get(i).asText())
                            .movePointLeft(6); // 除以1000000
                    BigDecimal lngDiff = new BigDecimal(polylineNode.get(i + 1).asText())
                            .movePointLeft(6); // 除以1000000

                    lat = lastLat.add(latDiff);
                    lng = lastLng.add(lngDiff);
                }

                lastLat = lat;
                lastLng = lng;

                List<BigDecimal> point = new ArrayList<>();
                point.add(lng); // 转换为[经度,纬度]格式返回
                point.add(lat);
                polyline.add(point);
            }
            routeResp.setPolyline(polyline);
            return Result.success(routeResp);

        } catch (Exception e) {
            throw new RuntimeException("路线规划失败: " + e.getMessage(), e);
        }
    }
}
