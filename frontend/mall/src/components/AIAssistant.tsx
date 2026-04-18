import { useState, useEffect, useRef } from "react";
import { MessageCircle, X, Send, Bot, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import ReactMarkdown from "react-markdown";
import { getCustomerToken } from "@/lib/api";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
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
    errorCode?: string | null;
    errorMessage?: string | null;
  };
}

type SseEvent =
  | { event: "start"; data: { sessionId: string } }
  | { event: "route"; data: { route?: string | null; reason?: string | null } }
  | { event: "delta"; data: { text: string } }
  | { event: "tool"; data: { name: string } }
  | { event: "final"; data: TaoChatResponse }
  | { event: "error"; data: { code: string; message: string } }
  | { event: "done"; data: Record<string, never> };

async function* parseSseStream(
  response: Response,
): AsyncGenerator<SseEvent, void, unknown> {
  if (!response.body) return;
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      let eventName = "message";
      let dataLine = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataLine += line.slice(5).trim();
        }
      }
      if (!dataLine) continue;
      try {
        const data = JSON.parse(dataLine);
        yield { event: eventName, data } as SseEvent;
      } catch {
        /* ignore malformed frame */
      }
    }
  }
}

const AIAssistant = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [tipIndex, setTipIndex] = useState(0);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 循环提示语
  const tips = [
    "有什么问题可以问我哦～",
    "我是您的专属瓷砖顾问！"
  ];

  // 循环显示提示语（当客服未展开时）
  useEffect(() => {
    if (!isOpen) {
      const interval = setInterval(() => {
        setTipIndex(prev => (prev + 1) % tips.length);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isOpen, tips.length]);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [messages]);

  // 生成唯一ID
  const generateId = () => {
    return Date.now().toString() + Math.random().toString(36).substr(2, 9);
  };

  // 生成或获取会话ID
  const getSessionId = async () => {
    let sessionId = localStorage.getItem('ai_chat_session_id');
    if (!sessionId) {
      sessionId = generateId();
      localStorage.setItem('ai_chat_session_id', sessionId);
    }
    return sessionId;
  };

  // 发送消息
  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const token = getCustomerToken();
    if (!token) {
      setMessages(prev => [
        ...prev,
        {
          id: generateId(),
          content: "请先登录商城账号，再使用智能客服为您查询订单、售后和商品信息。",
          isUser: false,
          timestamp: new Date(),
          status: "forbidden",
        }
      ]);
      return;
    }

    const userMessage: Message = {
      id: generateId(),
      content: inputValue.trim(),
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    // 创建AI消息占位符
    const aiMessageId = generateId();
    const aiMessage: Message = {
      id: aiMessageId,
      content: "",
      isUser: false,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, aiMessage]);

    try {
      const sessionId = await getSessionId(); // sessionId用作会话标识
      
      // 取消之前的请求
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      
      abortControllerRef.current = new AbortController();

      const response = await fetch("/pyapi/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "text/event-stream",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userMessage.content,
          sessionId,
          messageId: userMessage.id,
        }),
        signal: abortControllerRef.current?.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      let streamed = "";
      let collectedRoute: string | null = null;
      const collectedTools = new Set<string>();
      let errorText: string | null = null;

      for await (const ev of parseSseStream(response)) {
        if (ev.event === "start") {
          if (ev.data.sessionId) {
            localStorage.setItem('ai_chat_session_id', ev.data.sessionId);
          }
        } else if (ev.event === "route") {
          collectedRoute = ev.data.route ?? null;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === aiMessageId ? { ...msg, route: collectedRoute } : msg,
            ),
          );
        } else if (ev.event === "tool") {
          collectedTools.add(ev.data.name);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === aiMessageId
                ? { ...msg, toolCalls: Array.from(collectedTools) }
                : msg,
            ),
          );
        } else if (ev.event === "delta") {
          streamed += ev.data.text;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === aiMessageId ? { ...msg, content: streamed } : msg,
            ),
          );
        } else if (ev.event === "final") {
          const data = ev.data.data;
          if (data?.sessionId) {
            localStorage.setItem('ai_chat_session_id', data.sessionId);
          }
          const reply = (
            data?.answer ||
            data?.errorMessage ||
            streamed ||
            "抱歉，我暂时没有可用回复，请稍后再试。"
          ).trim();
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === aiMessageId
                ? {
                    ...msg,
                    content: reply,
                    route: data?.route ?? collectedRoute,
                    status: data?.status ?? "success",
                    toolCalls: data?.toolCalls ?? Array.from(collectedTools),
                  }
                : msg,
            ),
          );
        } else if (ev.event === "error") {
          errorText = ev.data.message || "流式会话异常";
        }
      }

      if (errorText) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMessageId
              ? { ...msg, content: streamed || errorText!, status: "error" }
              : msg,
          ),
        );
      }
      setIsLoading(false);

    } catch (error) {
      console.error('发送消息失败:', error);
      setMessages(prev =>
        prev.map(msg =>
          msg.id === aiMessageId
            ? { ...msg, content: "抱歉，我遇到了一些问题，请稍后再试。" }
            : msg
        )
      );
      setIsLoading(false);
    }
  };

  const handleNewConversation = () => {
    localStorage.removeItem('ai_chat_session_id');
    setMessages([]);
  };

  // 处理Enter键发送
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // 清理连接
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* 展开的聊天窗口 */}
      {isOpen && (
        <div className="absolute bottom-20 right-0 w-80 h-96 sm:w-96 sm:h-[500px] lg:w-[450px] lg:h-[600px] bg-white/95 backdrop-blur-xl rounded-lg shadow-2xl border border-gray-200/50 flex flex-col overflow-hidden">
          {/* 标题栏 */}
          <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg flex-shrink-0">
            <div className="flex items-center">
              <Bot className="h-5 w-5 mr-2" />
              <span className="font-medium">智能客服</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
              onClick={() => setIsOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* 消息区域 */}
          <div className="flex-1 min-h-0 p-4">
            <ScrollArea className="h-full" ref={scrollAreaRef}>
              <div className="space-y-3 pr-4">
                {messages.length === 0 && (
                  <div className="text-center text-gray-500 text-sm py-8">
                    <Bot className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                    <p>您好！我是您的专属瓷砖顾问</p>
                    <p>有什么问题可以随时问我～</p>
                  </div>
                )}
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[75%] px-3 py-2 rounded-lg ${
                        message.isUser
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      <div className="flex items-start space-x-2">
                        {!message.isUser && (
                          <Bot className="h-4 w-4 mt-0.5 flex-shrink-0 text-blue-500" />
                        )}
                        {message.content ? (
                          <ReactMarkdown className="prose prose-sm max-w-none whitespace-pre-wrap">
                            {message.content}
                          </ReactMarkdown>
                        ) : (
                          <div className="text-sm whitespace-pre-wrap">
                            {isLoading ? "思考中..." : ""}
                          </div>
                        )}
                      </div>
                      {!message.isUser && (message.route || message.status || (message.toolCalls && message.toolCalls.length > 0)) && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {message.route && (
                            <span className="rounded-full bg-white/70 px-2 py-0.5 text-[11px] text-slate-700">
                              路由: {message.route}
                            </span>
                          )}
                          {message.status && (
                            <span className="rounded-full bg-white/70 px-2 py-0.5 text-[11px] text-slate-700">
                              状态: {message.status}
                            </span>
                          )}
                          {message.toolCalls && message.toolCalls.length > 0 && (
                            <span className="rounded-full bg-white/70 px-2 py-0.5 text-[11px] text-slate-700">
                              工具: {message.toolCalls.join(", ")}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
          
          {/* 输入区域 */}
          <div className="p-4 border-t border-gray-200 flex-shrink-0">
            <div className="flex space-x-2">
              <Button
                onClick={handleNewConversation}
                disabled={isLoading}
                size="icon"
                variant="outline"
                className="flex-shrink-0"
                title="开始新会话"
              >
                <Plus className="h-4 w-4" />
              </Button>
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={getCustomerToken() ? "输入您的问题..." : "登录后可使用智能客服"}
                disabled={isLoading}
                className="flex-1"
              />
              <Button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isLoading}
                size="icon"
                className="bg-blue-600 hover:bg-blue-700 flex-shrink-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 悬浮按钮 - 始终保持在固定位置 */}
      <Button
        onClick={() => setIsOpen(!isOpen)}
        className="h-14 w-14 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-110"
        size="icon"
      >
        <MessageCircle className="h-6 w-6 text-white" />
      </Button>
      
      {/* 提示语气泡 */}
      {!isOpen && (
        <div className="absolute bottom-full right-0 mb-2 animate-bounce">
          <div className="bg-white/95 backdrop-blur-xl text-gray-800 px-3 py-2 rounded-lg shadow-lg border border-gray-200/50 whitespace-nowrap text-sm">
            {tips[tipIndex]}
            <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-white/95"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAssistant; 
