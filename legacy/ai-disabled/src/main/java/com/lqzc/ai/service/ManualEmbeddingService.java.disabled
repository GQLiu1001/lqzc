package com.lqzc.ai.service;

import org.springframework.ai.document.Document;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class ManualEmbeddingService {

    private final EmbeddingModel embeddingModel;

    public ManualEmbeddingService(EmbeddingModel embeddingModel) {
        this.embeddingModel = embeddingModel;
    }

    /**
     * 1) 直接对字符串做 embedding，返回 List<Float>
     */
    public List<Float> embedText(String text) {
        // 你当前版本的 EmbeddingModel.embed(...) 返回的是 float[]
        float[] vec = embeddingModel.embed(text);

        List<Float> result = new ArrayList<>(vec.length);
        for (float v : vec) {
            result.add(v);
        }
        return result;
    }

    /**
     * 2) 携带 metadata 的 Document embedding
     */
    public List<Float> embedDocument(String content, String manualId) {
        Document doc = new Document(content);
        doc.getMetadata().put("manualId", manualId);

        // 这里同样返回的是 float[]
        float[] vec = embeddingModel.embed(doc);

        List<Float> result = new ArrayList<>(vec.length);
        for (float v : vec) {
            result.add(v);
        }
        return result;
    }
}
