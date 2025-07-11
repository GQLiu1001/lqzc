package com.lqzc.config;

import cn.binarywang.wx.miniapp.api.WxMaService;
import cn.binarywang.wx.miniapp.api.impl.WxMaServiceImpl;
import cn.binarywang.wx.miniapp.config.impl.WxMaDefaultConfigImpl;
import com.lqzc.common.props.WxConfigProperties;
import jakarta.annotation.Resource;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

@Component
public class WxConfig {

    @Resource
    private WxConfigProperties wxConfigProperties;
    @Bean
    public WxMaService wxMaService() {
        WxMaService service = new WxMaServiceImpl();
        WxMaDefaultConfigImpl config =new WxMaDefaultConfigImpl();
        config.setAppid(wxConfigProperties.getAppId());
        config.setSecret(wxConfigProperties.getSecret());
        service.setWxMaConfig(config);
        return service;
    }
}
