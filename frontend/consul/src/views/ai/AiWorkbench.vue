<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/stores/user';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  route?: string | null;
  status?: string;
  toolCalls?: string[];
}

interface TaoChatResponse {
  code: number;
  message: string;
  data: {
    sessionId: string;
    route?: string | null;
    answer?: string | null;
    toolCalls?: string[];
    status: string;
    interrupt?: {
      id?: string;
      tool?: string;
      args?: Record<string, unknown>;
      description?: string;
      allowedDecisions?: string[];
    } | null;
    errorCode?: string | null;
    errorMessage?: string | null;
  };
}

interface RagSummary {
  documents: number;
  chunks: number;
  domains: Record<string, number>;
  cachePath: string;
  milvus?: {
    available: boolean;
    message: string;
  };
}

const userStore = useUserStore();
const inputValue = ref('');
const messages = ref<ChatMessage[]>([]);
const isSending = ref(false);
const isRefreshing = ref(false);
const isReindexing = ref(false);
const ragSummary = ref<RagSummary | null>(null);
const decisionComment = ref('');
const pendingInterrupt = ref<TaoChatResponse['data']['interrupt']>(null);

const sessionStorageKey = 'consul_ai_chat_session_id';

const currentUser = computed(() => userStore.getUserInfo());
const sessionId = ref(localStorage.getItem(sessionStorageKey) || `consul-${Date.now()}`);

const generateId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const authHeaders = (): Record<string, string> => {
  const token = userStore.getToken();
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
};

const appendAssistantMessage = (payload: TaoChatResponse['data']) => {
  messages.value.push({
    id: generateId(),
    role: 'assistant',
    content: (payload.answer || payload.errorMessage || '当前没有可展示的回复。').trim(),
    createdAt: new Date().toLocaleTimeString(),
    route: payload.route ?? null,
    status: payload.status,
    toolCalls: payload.toolCalls ?? [],
  });
  pendingInterrupt.value = payload.interrupt ?? null;
};

type SseFrame =
  | { event: 'start'; data: { sessionId: string } }
  | { event: 'route'; data: { route?: string | null; reason?: string | null } }
  | { event: 'delta'; data: { text: string } }
  | { event: 'tool'; data: { name: string } }
  | { event: 'final'; data: TaoChatResponse }
  | { event: 'error'; data: { code: string; message: string } }
  | { event: 'done'; data: Record<string, never> };

async function* parseSseStream(response: Response): AsyncGenerator<SseFrame, void, unknown> {
  if (!response.body) return;
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      let eventName = 'message';
      let dataLine = '';
      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          dataLine += line.slice(5).trim();
        }
      }
      if (!dataLine) continue;
      try {
        yield { event: eventName, data: JSON.parse(dataLine) } as SseFrame;
      } catch (err) {
        console.warn('SSE frame parse failed', err);
      }
    }
  }
}

const resetConversation = () => {
  sessionId.value = `consul-${Date.now()}`;
  localStorage.setItem(sessionStorageKey, sessionId.value);
  messages.value = [];
  pendingInterrupt.value = null;
  decisionComment.value = '';
};

const sendMessage = async () => {
  if (!inputValue.value.trim() || isSending.value) {
    return;
  }

  const messageText = inputValue.value.trim();
  const messageId = generateId();
  messages.value.push({
    id: messageId,
    role: 'user',
    content: messageText,
    createdAt: new Date().toLocaleTimeString(),
  });
  inputValue.value = '';
  isSending.value = true;

  const assistantId = generateId();
  const assistantMessage: ChatMessage = {
    id: assistantId,
    role: 'assistant',
    content: '',
    createdAt: new Date().toLocaleTimeString(),
    route: null,
    status: 'streaming',
    toolCalls: [],
  };
  messages.value.push(assistantMessage);

  const updateAssistant = (patch: Partial<ChatMessage>) => {
    const target = messages.value.find((msg) => msg.id === assistantId);
    if (target) Object.assign(target, patch);
  };

  try {
    const response = await fetch('/pyapi/chat/stream', {
      method: 'POST',
      headers: {
        ...authHeaders(),
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({
        sessionId: sessionId.value,
        messageId,
        message: messageText,
      }),
    });

    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`);
    }

    let streamed = '';
    const tools = new Set<string>();
    let errorMessage: string | null = null;
    let finalData: TaoChatResponse['data'] | null = null;

    for await (const ev of parseSseStream(response)) {
      if (ev.event === 'start') {
        if (ev.data.sessionId) {
          sessionId.value = ev.data.sessionId;
          localStorage.setItem(sessionStorageKey, ev.data.sessionId);
        }
      } else if (ev.event === 'route') {
        updateAssistant({ route: ev.data.route ?? null });
      } else if (ev.event === 'tool') {
        tools.add(ev.data.name);
        updateAssistant({ toolCalls: Array.from(tools) });
      } else if (ev.event === 'delta') {
        streamed += ev.data.text;
        updateAssistant({ content: streamed });
      } else if (ev.event === 'final') {
        finalData = ev.data.data;
      } else if (ev.event === 'error') {
        errorMessage = ev.data.message || '流式会话异常';
      }
    }

    if (errorMessage && !finalData) {
      throw new Error(errorMessage);
    }

    if (finalData) {
      if (finalData.sessionId) {
        sessionId.value = finalData.sessionId;
        localStorage.setItem(sessionStorageKey, finalData.sessionId);
      }
      updateAssistant({
        content: (finalData.answer || finalData.errorMessage || streamed || '当前没有可展示的回复。').trim(),
        route: finalData.route ?? null,
        status: finalData.status,
        toolCalls: finalData.toolCalls ?? Array.from(tools),
      });
      pendingInterrupt.value = finalData.interrupt ?? null;
    } else {
      updateAssistant({ status: 'success' });
    }
  } catch (error) {
    console.error('AI 对话失败:', error);
    ElMessage.error((error as Error).message || 'AI 对话失败');
    updateAssistant({
      content: '当前请求失败，请检查 FastAPI 服务与登录态是否正常。',
      status: 'error',
    });
  } finally {
    isSending.value = false;
  }
};

const submitDecision = async (decision: 'approve' | 'reject') => {
  if (!pendingInterrupt.value?.tool || !pendingInterrupt.value?.id) {
    ElMessage.warning('当前没有待处理审批');
    return;
  }

  isSending.value = true;
  try {
    const response = await fetch('/pyapi/chat/interrupt/decision', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        sessionId: sessionId.value,
        decision,
        tool: pendingInterrupt.value.tool,
        comment: decisionComment.value || undefined,
      }),
    });

    const result = (await response.json()) as TaoChatResponse;
    if (!response.ok || result.code !== 200) {
      throw new Error(result.data?.errorMessage || result.message || `审批失败: ${response.status}`);
    }

    appendAssistantMessage(result.data);
    pendingInterrupt.value = result.data.interrupt ?? null;
    decisionComment.value = '';
    ElMessage.success(decision === 'approve' ? '已提交通过' : '已提交拒绝');
  } catch (error) {
    console.error('审批提交失败:', error);
    ElMessage.error((error as Error).message || '审批提交失败');
  } finally {
    isSending.value = false;
  }
};

const refreshSummary = async () => {
  isRefreshing.value = true;
  try {
    const response = await fetch('/pyapi/rag/summary', {
      headers: {
        Authorization: `Bearer ${userStore.getToken()}`,
      },
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || `获取索引概况失败: ${response.status}`);
    }
    ragSummary.value = result as RagSummary;
  } catch (error) {
    console.error('获取 RAG 概况失败:', error);
    ElMessage.error((error as Error).message || '获取 RAG 概况失败');
  } finally {
    isRefreshing.value = false;
  }
};

const reindexRag = async () => {
  isReindexing.value = true;
  try {
    const response = await fetch('/pyapi/rag/reindex', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        forceRefresh: true,
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || `RAG 重建失败: ${response.status}`);
    }
    ElMessage.success('RAG 重建已完成');
    ragSummary.value = result as RagSummary;
  } catch (error) {
    console.error('RAG 重建失败:', error);
    ElMessage.error((error as Error).message || 'RAG 重建失败');
  } finally {
    isReindexing.value = false;
  }
};

onMounted(() => {
  localStorage.setItem(sessionStorageKey, sessionId.value);
  refreshSummary();
});
</script>

<template>
  <div class="ai-workbench">
    <el-row :gutter="16">
      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="chat-card">
          <template #header>
            <div class="card-header">
              <div>
                <div class="title">AI 工作台</div>
                <div class="subtitle">统一接入 FastAPI `/chat`，支持商城问答、仓储问答与审批恢复。</div>
              </div>
              <div class="header-actions">
                <el-tag type="info">session: {{ sessionId }}</el-tag>
                <el-button plain @click="resetConversation">新会话</el-button>
              </div>
            </div>
          </template>

          <div class="chat-messages">
            <div v-if="messages.length === 0" class="empty-state">
              <div class="empty-title">后台 AI 助手已接入</div>
              <div class="empty-text">你可以直接问订单、库存、审批或 RAG 命中的问题。</div>
            </div>

            <div
              v-for="message in messages"
              :key="message.id"
              :class="['message-row', message.role === 'user' ? 'user' : 'assistant']"
            >
              <div :class="['message-bubble', message.role === 'user' ? 'user' : 'assistant']">
                <div class="message-content">{{ message.content }}</div>
                <div v-if="message.role === 'assistant'" class="meta-row">
                  <el-tag v-if="message.route" size="small" type="info">route: {{ message.route }}</el-tag>
                  <el-tag v-if="message.status" size="small" :type="message.status === 'success' ? 'success' : 'warning'">
                    {{ message.status }}
                  </el-tag>
                  <el-tag
                    v-for="tool in message.toolCalls || []"
                    :key="tool"
                    size="small"
                    type="primary"
                  >
                    {{ tool }}
                  </el-tag>
                </div>
                <div class="message-time">{{ message.createdAt }}</div>
              </div>
            </div>
          </div>

          <div class="chat-composer">
            <el-input
              v-model="inputValue"
              type="textarea"
              :rows="3"
              resize="none"
              placeholder="输入后台问题，例如：查一下仓库 3 的 TA800-01 库存，或者帮我解释售后规则。"
              @keydown.ctrl.enter.prevent="sendMessage"
            />
            <div class="composer-actions">
              <span class="hint">Ctrl + Enter 发送</span>
              <el-button type="primary" :loading="isSending" @click="sendMessage">发送</el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div class="side-stack">
          <el-card shadow="never">
            <template #header>
              <div class="side-title">RAG 索引概况</div>
            </template>
            <div class="summary-grid">
              <div class="summary-item">
                <div class="summary-label">文档数</div>
                <div class="summary-value">{{ ragSummary?.documents ?? '-' }}</div>
              </div>
              <div class="summary-item">
                <div class="summary-label">Chunk 数</div>
                <div class="summary-value">{{ ragSummary?.chunks ?? '-' }}</div>
              </div>
            </div>
            <div class="domain-list" v-if="ragSummary?.domains">
              <el-tag
                v-for="(count, domain) in ragSummary.domains"
                :key="domain"
                class="domain-tag"
                type="info"
              >
                {{ domain }}: {{ count }}
              </el-tag>
            </div>
            <div class="milvus-state">
              <el-tag :type="ragSummary?.milvus?.available ? 'success' : 'danger'">
                Milvus {{ ragSummary?.milvus?.available ? '可用' : '不可用' }}
              </el-tag>
              <div class="milvus-message">{{ ragSummary?.milvus?.message || '暂无状态' }}</div>
            </div>
            <div class="summary-actions">
              <el-button :loading="isRefreshing" @click="refreshSummary">刷新概况</el-button>
              <el-button type="primary" :loading="isReindexing" @click="reindexRag">强制重建</el-button>
            </div>
          </el-card>

          <el-card shadow="never" v-if="pendingInterrupt">
            <template #header>
              <div class="side-title">待审批动作</div>
            </template>
            <div class="interrupt-body">
              <div><strong>工具：</strong>{{ pendingInterrupt.tool || '-' }}</div>
              <div><strong>说明：</strong>{{ pendingInterrupt.description || '无' }}</div>
              <div><strong>参数：</strong>{{ JSON.stringify(pendingInterrupt.args || {}, null, 2) }}</div>
              <el-input
                v-model="decisionComment"
                type="textarea"
                :rows="3"
                resize="none"
                placeholder="可选：填写审批备注"
              />
              <div class="summary-actions">
                <el-button type="success" :loading="isSending" @click="submitDecision('approve')">批准</el-button>
                <el-button type="danger" :loading="isSending" @click="submitDecision('reject')">拒绝</el-button>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.ai-workbench {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-card {
  min-height: 720px;
}

.card-header,
.header-actions,
.summary-actions,
.meta-row,
.summary-grid,
.side-stack {
  display: flex;
  gap: 12px;
}

.card-header {
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
}

.header-actions {
  align-items: center;
  flex-wrap: wrap;
}

.title,
.side-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.subtitle,
.hint,
.message-time,
.milvus-message,
.empty-text {
  color: #6b7280;
  font-size: 13px;
}

.chat-messages {
  height: 500px;
  overflow-y: auto;
  padding: 8px 4px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message-row {
  display: flex;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 78%;
  padding: 14px 16px;
  border-radius: 18px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.message-bubble.user {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
}

.message-bubble.assistant {
  background: #f8fafc;
  color: #111827;
  border: 1px solid #e5e7eb;
}

.message-content {
  white-space: pre-wrap;
  line-height: 1.65;
}

.meta-row {
  flex-wrap: wrap;
  margin-top: 10px;
}

.message-time {
  margin-top: 8px;
}

.chat-composer {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.empty-state {
  height: 100%;
  min-height: 180px;
  border: 1px dashed #d1d5db;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  background: linear-gradient(180deg, #f8fafc, #eef2ff);
}

.empty-title,
.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.summary-grid {
  justify-content: space-between;
}

.summary-item {
  flex: 1;
  padding: 16px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}

.summary-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.domain-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
}

.milvus-state {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.interrupt-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}

.side-stack {
  flex-direction: column;
}

@media (max-width: 1024px) {
  .chat-card {
    min-height: auto;
  }

  .chat-messages {
    height: 420px;
  }
}
</style>
