package com.lqzc.ai.service;

import io.milvus.client.MilvusServiceClient;
import io.milvus.grpc.SearchResults;
import io.milvus.param.MetricType;
import io.milvus.param.R;
import io.milvus.param.dml.SearchParam;
import io.milvus.response.SearchResultsWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ManualSearchService {

    private final ManualEmbeddingService embeddingService;
    private final MilvusServiceClient milvusClient;

    /**
     * 查询 Milvus，返回与问题最相关的片段
     */
    public List<ManualHit> search(String question, int topK) {
        List<Float> queryEmb = embeddingService.embedText(question);
        List<List<Float>> vectors = Collections.singletonList(queryEmb);

        int limit = Math.max(topK, 1);

        @SuppressWarnings("deprecation")
        SearchParam searchParam = SearchParam.newBuilder()
                .withDatabaseName("lqzc_db")
                .withCollectionName("manual_rag")
                .withMetricType(MetricType.COSINE)
                .withOutFields(List.of("manual_id", "content", "chunk_index"))
                .withTopK(limit)
                .withVectors(vectors)
                .withVectorFieldName("embedding")
                .withParams("{\"nprobe\": 10}")
                .build();

        R<SearchResults> result = milvusClient.search(searchParam);
        if (result == null || result.getData() == null || result.getData().getResults() == null) {
            return Collections.emptyList();
        }

        SearchResults data = result.getData();
        SearchResultsWrapper wrapper = new SearchResultsWrapper(data.getResults());

        List<ManualHit> hits = new ArrayList<>();
        for (int i = 0; i < vectors.size(); i++) { // 当前只查询一个问题
            List<SearchResultsWrapper.IDScore> scores = wrapper.getIDScore(i);
            for (SearchResultsWrapper.IDScore s : scores) {
                hits.add(new ManualHit(
                        (String) s.get("manual_id"),
                        (Long) s.get("chunk_index"),
                        (String) s.get("content"),
                        s.getScore()
                ));
            }
        }
        return hits;
    }

    public void testSearch(String question) {
        List<ManualHit> hits = search(question, 5);
        System.out.println("======= 搜索结果 =======");
        for (ManualHit hit : hits) {
            System.out.printf(
                    "manualId=%s, chunkIndex=%d, score=%.4f%n内容: %s%n%n",
                    hit.manualId(), hit.chunkIndex(), hit.score(), hit.content()
            );
        }
        System.out.println("=======================");
    }

    public record ManualHit(String manualId, Long chunkIndex, String content, Float score) {
    }
}
