package com.lqzc.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.lqzc.common.Result;
import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.req.CartDeleteReq;
import com.lqzc.common.req.CartReq;
import com.lqzc.common.req.MallOrderReq;
import com.lqzc.common.resp.CartItemsResp;
import com.lqzc.utils.UserContextHolder;
import com.lqzc.service.InventoryItemService;
import com.lqzc.service.SelectionItemService;
import com.lqzc.service.SelectionListService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Tag(name = "商城系统购物车相关接口")
@RestController
@RequestMapping("/mall/cart")
public class CartController {

    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private SelectionItemService selectionItemService;
    @Resource
    private SelectionListService selectionListService;
    @Resource
    private ObjectMapper objectMapper;
    @Resource
    private InventoryItemService inventoryItemService;

    @Operation(summary = "获取购物车展示信息")
    @GetMapping
    public Result<List<CartItemsResp>> getCartInfo() {
        String cartId = UserContextHolder.getCartId();
        Map<Object, Object> cartEntries = stringRedisTemplate.opsForHash().entries(RedisConstant.CART_ID+cartId);
        if (CollectionUtils.isEmpty(cartEntries)) {
            return Result.success();
        }
        List<CartItemsResp> resps = cartEntries.entrySet().stream()
                .map(entry -> {
                    String model = (String) entry.getKey();
                    String json = (String) entry.getValue();
                    CartItemsResp jsonValue = null;
                    try {
                        jsonValue = objectMapper.readValue(json, CartItemsResp.class);
                    } catch (JsonProcessingException e) {
                        System.out.println("e = " + e);
                        throw new LianqingException(e.getMessage());
                    }
                    CartItemsResp resp = new CartItemsResp();
                    resp.setModel(model);
                    resp.setAmount(jsonValue.getAmount());
                    return resp;
                })
                .toList();
        return Result.success(resps);
    }

    @Operation(summary = "加到购物车信息")
    @PostMapping("/add")
    public Result<?> addCart(@RequestBody CartReq cartReq)  {
        try {
            String cartId = UserContextHolder.getCartId();
            String key = RedisConstant.CART_ID + cartId;
            String value = objectMapper.writeValueAsString(cartReq);
            stringRedisTemplate.opsForHash().put(key, cartReq.getModel(), value);
            stringRedisTemplate.expire(key,30, TimeUnit.DAYS);
        } catch (JsonProcessingException e) {
            System.out.println("e = " + e);
            throw new LianqingException();
        }
        return Result.success();
    }


    @Operation(summary = "修改购物车信息")
    @PostMapping("/change")
    public Result<?> changeCart(@RequestBody CartReq cartReq)  {
        try {
            String cartId = UserContextHolder.getCartId();
            String key = RedisConstant.CART_ID + cartId;
            stringRedisTemplate.opsForHash().delete(key, cartReq.getModel());
            String value = objectMapper.writeValueAsString(cartReq);
            stringRedisTemplate.opsForHash().put(key, cartReq.getModel(), value);
            stringRedisTemplate.expire(key,30, TimeUnit.DAYS);
        } catch (JsonProcessingException e) {
            System.out.println("e = " + e);
            throw new LianqingException();
        }
        return Result.success();
    }

    @Operation(summary = "删除购物车信息")
    @DeleteMapping("/delete")
    public Result<?> deleteCart(@RequestBody CartDeleteReq cartDeleteReq) {
        String cartId = UserContextHolder.getCartId();
        stringRedisTemplate.opsForHash().delete(RedisConstant.CART_ID + cartId, cartDeleteReq.getModel());
        return Result.success();
    }

    @Transactional(rollbackFor = Exception.class)
    @Operation(summary = "购物车下单")
    @PostMapping("/order")
    public Result<?> order(@RequestBody MallOrderReq mallOrderReq) {
        Long id = selectionListService.addSellectionList(mallOrderReq);
        selectionItemService.addSellectionListItems(mallOrderReq,id);
        String cartId = UserContextHolder.getCartId();
        String key = RedisConstant.CART_ID + cartId;
        stringRedisTemplate.delete(key);
        return Result.success();
    }
}
