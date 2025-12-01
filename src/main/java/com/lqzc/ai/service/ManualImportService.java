package com.lqzc.ai.service;

import io.milvus.client.MilvusServiceClient;
import io.milvus.grpc.MutationResult;
import io.milvus.param.R;
import io.milvus.param.dml.InsertParam;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.*;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ManualImportService {

    private final ManualEmbeddingService embeddingService;
    private final MilvusServiceClient milvusClient;

    /**
     * 扫描 resources/manuals 目录，把所有 txt 导入 Milvus
     */
    public void importAll() throws IOException {
        Path dir = Paths.get("src/main/resources/manuals");

        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*.txt")) {
            for (Path file : stream) {
                String name = file.getFileName().toString();
                String content = Files.readString(file);
                importOneManual(name, content);
            }
        }
    }

    /**
     * 单个文件导入
     */
    public void importOneManual(String manualId, String content) {
        List<String> chunks = split(content, 500);

        List<InsertParam.Field> fields = new ArrayList<>();

        // 准备批量数据（一次性插整本手册）
        List<String> manualIds = new ArrayList<>();
        List<Long> chunkIndexes = new ArrayList<>();
        List<String> contents = new ArrayList<>();
        List<List<Float>> embeddings = new ArrayList<>();

        long index = 0;
        for (String chunk : chunks) {
            index++;
            manualIds.add(manualId);
            chunkIndexes.add(index);
            contents.add(chunk);

            List<Float> vec = embeddingService.embedText(chunk);
            embeddings.add(vec);
        }

        fields.add(new InsertParam.Field("manual_id", manualIds));
        fields.add(new InsertParam.Field("chunk_index", chunkIndexes));
        fields.add(new InsertParam.Field("content", contents));
        fields.add(new InsertParam.Field("embedding", embeddings)); // List<List<Float>>

        InsertParam insertParam = InsertParam.newBuilder()
                .withCollectionName("manual_rag")
                .withFields(fields)
                .build();

        R<MutationResult> res = milvusClient.insert(insertParam);
        // 你可以加日志：res.getStatus() 看看是否成功
        System.out.println(res.toString());
    }

    /**
     * 简单按字数切块
     */
    private List<String> split(String s, int size) {
        List<String> list = new ArrayList<>();
        int length = s.length();
        for (int i = 0; i < length; i += size) {
            list.add(s.substring(i, Math.min(length, i + size)));
        }
        return list;
    }
}
