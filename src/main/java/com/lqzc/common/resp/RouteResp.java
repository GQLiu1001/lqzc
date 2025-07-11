package com.lqzc.common.resp;

import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

/**
 * 腾讯地图路线规划响应类
 */
@Data
public class RouteResp {
    /**
     * 距离（米）
     */
    private Integer distance;
    
    /**
     * 时长（秒）
     */
    private Integer duration;
    
    /**
     * 路线坐标点集合（压缩后的坐标数组，包含纬度和经度）
     * 格式：[纬度1, 经度1, 纬度2, 经度2, ...]
     */
    private List<List<BigDecimal>> polyline;
}
