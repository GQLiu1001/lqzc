package com.lqzc.common.props;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@Data
@ConfigurationProperties(prefix = "wx.miniapp")
public class WxConfigProperties {
    private String appId;
    private String secret;
    private String map;
    private String tencentMapApi = "https://apis.map.qq.com/ws/direction/v1/driving/";
}
