package com.lqzc.common.req;

import lombok.Data;

@Data
public class AddressAddReq {
    /** 收货人 */
    private String receiverName;
    /** 收货人手机号 */
    private String receiverPhone;
    /** 省 */
    private String province;
    /** 市 */
    private String city;
    /** 区县 */
    private String district;
    /** 详细地址 */
    private String detail;
    /** 标签（家/公司/工地） */
    private String tag;
    /** 是否默认 0/1 */
    private Integer isDefault;
    /** 纬度 */
    private Double latitude;
    /** 经度 */
    private Double longitude;
}
