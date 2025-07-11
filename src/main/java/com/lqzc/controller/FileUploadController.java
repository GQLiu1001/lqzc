package com.lqzc.controller;

import com.lqzc.common.domain.InventoryItem;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.center.R2StorageCenter;
import com.lqzc.service.InventoryItemService;
import jakarta.annotation.Resource;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/upload") // 你可以自定义接口的基础路径
@RequiredArgsConstructor
public class FileUploadController {

    @Resource
    private R2StorageCenter r2StorageCenter;
    @Resource
    private InventoryItemService inventoryItemService;
    /**
     * 图片上传接口
     * @param file 前端通过表单提交的文件，参数名必须为 "file"
     * @return 返回一个包含图片URL的JSON对象
     */
    @PostMapping("/image")
    public ResponseEntity<?> uploadImage(@RequestBody MultipartFile file, @RequestParam("itemId")Long itemId) {
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body("请选择一个文件进行上传");
        }

        // 调用Service层执行上传
        String fileUrl = r2StorageCenter.uploadFile(file);

        // 构建一个标准的JSON返回体
        Map<String, String> response = new HashMap<>();
        response.put("url", fileUrl);
        InventoryItem byId = inventoryItemService.getById(itemId);
        byId.setPicture(fileUrl);
        boolean b = inventoryItemService.updateById(byId);
        if (!b){
            throw new LianqingException("更新照片失败");
        }
        // HTTP 200 OK, body: {"url": "https://pub-....r2.dev/....jpg"}
        return ResponseEntity.ok(response);
    }
}
