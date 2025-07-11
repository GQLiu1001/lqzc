package com.lqzc.center;

import com.amazonaws.auth.AWSCredentials;
import com.amazonaws.auth.AWSStaticCredentialsProvider;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.client.builder.AwsClientBuilder;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.ObjectMetadata;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;


@Slf4j
@Service
public class R2StorageCenter {

    private final AmazonS3 s3client;

    @Value("${cloudflare.r2.bucket-name}")
    private String bucketName;

    @Value("${cloudflare.r2.public-url}")
    private String publicUrl;

    // 支持的图片格式
    private static final List<String> ALLOWED_IMAGE_TYPES = Arrays.asList(
            "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"
    );

    // 支持的文件扩展名
    private static final List<String> ALLOWED_EXTENSIONS = Arrays.asList(
            ".jpg", ".jpeg", ".png", ".gif", ".webp"
    );

    // 最大文件大小：5MB
    private static final long MAX_FILE_SIZE = 5 * 1024 * 1024;

    /**
     * 构造函数，Spring会自动调用它并注入参数
     */
    public R2StorageCenter(@Value("${cloudflare.r2.endpoint}") String endpoint,
                           @Value("${cloudflare.r2.access-key-id}") String accessKeyId,
                           @Value("${cloudflare.r2.secret-access-key}") String secretAccessKey) {

        log.info("初始化R2存储中心，端点: {}, 存储桶: {}", endpoint, bucketName);

        // 设置访问凭证
        AWSCredentials credentials = new BasicAWSCredentials(accessKeyId, secretAccessKey);

        // 设置R2的API端点
        AwsClientBuilder.EndpointConfiguration endpointConfiguration =
                new AwsClientBuilder.EndpointConfiguration(endpoint, "auto");

        // 构建S3客户端
        this.s3client = AmazonS3ClientBuilder.standard()
                .withCredentials(new AWSStaticCredentialsProvider(credentials))
                .withEndpointConfiguration(endpointConfiguration)
                .withPathStyleAccessEnabled(true) // R2需要启用路径样式访问
                .build();

        log.info("R2存储中心初始化完成");
    }

    /**
     * 上传文件到R2，并返回最终可公开访问的URL。
     *
     * @param file 从Controller层传递过来的文件对象
     * @return 上传成功后文件的完整URL
     */
    public String uploadFile(MultipartFile file) {
        try {
            // 1. 生成一个唯一的文件名，避免文件名冲突
            String originalFilename = file.getOriginalFilename();
            // 安全地获取文件扩展名
            String fileExtension = "";
            if (originalFilename != null && originalFilename.contains(".")) {
                fileExtension = originalFilename.substring(originalFilename.lastIndexOf("."));
            }
            String uniqueFileName = UUID.randomUUID().toString() + fileExtension;

            // 2. 获取文件的输入流和元数据 (如文件类型、大小)
            InputStream inputStream = file.getInputStream();
            ObjectMetadata metadata = new ObjectMetadata();
            metadata.setContentLength(file.getSize());
            metadata.setContentType(file.getContentType());

            // 3. 执行上传操作
            s3client.putObject(bucketName, uniqueFileName, inputStream, metadata);

            // 4. 拼接并返回最终的URL
            return publicUrl + "/" + uniqueFileName;

        } catch (Exception e) {
            // 在真实项目中，应该使用更完善的日志和异常处理机制
            e.printStackTrace();
            throw new RuntimeException("文件上传到R2失败", e);
        }
    }
}
