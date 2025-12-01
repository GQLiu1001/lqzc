package com.lqzc.ai.service;

import io.milvus.client.MilvusServiceClient;
import io.milvus.grpc.SearchResults;
import io.milvus.param.MetricType;
import io.milvus.param.R;
import io.milvus.param.dml.SearchParam;
import io.milvus.response.SearchResultsWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ManualSearchService {

    private final ManualEmbeddingService embeddingService;
    private final MilvusServiceClient milvusClient;

    public void testSearch(String question) {
        // 1. 生成查询向量（和你写入 Milvus 的 embedding 维度一致）
        List<Float> queryEmb = embeddingService.embedText(question);

        // 2. Milvus 需要 List<List<Float>>，外面再包一层 List
        List<List<Float>> vectors = Collections.singletonList(queryEmb);

        // 3. 构造搜索参数
        @SuppressWarnings("deprecation") // 如果你不想看到黄色警告，可以加这一句
        SearchParam searchParam = SearchParam.newBuilder()
                .withDatabaseName("lqzc_db")
                .withCollectionName("manual_rag")                  // 你现在插的就是这个集合
                .withMetricType(MetricType.COSINE)                   // 和建表时 metric 保持一致
                .withOutFields(List.of("manual_id", "content", "chunk_index"))
                .withTopK(5)                                       // SDK 的签名是 Integer
                .withVectors(vectors)                              // 这里用我们刚刚构造的 vectors
                .withVectorFieldName("embedding")                  // 跟建集合的向量字段名一致
                .withParams("{\"nprobe\": 10}")                    // 常规 IVF 参数
                .build();

        // 4. 执行搜索
        R<SearchResults> result = milvusClient.search(searchParam);
        SearchResults data = result.getData();
        SearchResultsWrapper wrapper = new SearchResultsWrapper(data.getResults());

        System.out.println("======= 搜索结果 =======");
        for (int i = 0; i < vectors.size(); i++) { // 现在就 1 个 query
            List<SearchResultsWrapper.IDScore> scores = wrapper.getIDScore(i);
            for (SearchResultsWrapper.IDScore s : scores) {
                Long id = s.getLongID();
                Float score = s.getScore();
                String manualId = (String) s.get("manual_id");
                String content = (String) s.get("content");
                Long chunkIndex = (Long) s.get("chunk_index");

                System.out.printf(
                        "pk=%d, score=%.4f, manualId=%s, chunkIndex=%d%n内容: %s%n%n",
                        id, score, manualId, chunkIndex, content
                );
            }
        }
        System.out.println("=======================");
    }
}
