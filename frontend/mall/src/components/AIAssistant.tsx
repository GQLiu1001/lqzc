import { useState, useEffect, useRef } from "react";
import { MessageCircle, X, Send, Bot, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getCustomerToken, isLoggedIn } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
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

    // 检查是否已登录
    if (!isLoggedIn()) {
      const loginHintMessage: Message = {
        id: generateId(),
        content: "请先登录后再使用智能客服功能～ 点击右上角的用户图标进行登录。",
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, loginHintMessage]);
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
      
      // 构建请求头（如果已登录则带上token）
      const headers: Record<string, string> = {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      };
      
      const customerToken = getCustomerToken();
      if (customerToken) {
        headers['X-Customer-Token'] = customerToken;
      }
      
      const response = await fetch(`/api/mall/ai/stream-chat?message=${encodeURIComponent(userMessage.content)}&sessionId=${encodeURIComponent(sessionId)}`, {
        method: 'GET',
        headers,
        signal: abortControllerRef.current?.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法获取响应流');
      }

      const decoder = new TextDecoder();
      let fullContent = "";
      let buffer = "";

      // 读取流数据
      const readStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const events = buffer.split("\n\n");
            buffer = events.pop() || "";

            for (const event of events) {
              const dataLines = event
                .split("\n")
                .filter((line) => line.startsWith("data:"));

              if (dataLines.length === 0) continue;

              const data = dataLines
                  .map((line) => line.slice(5))
                  .join("\n");

              if (data === "[DONE]") {
                reader.cancel();
                return;
              }

              fullContent += data;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === aiMessageId ? { ...msg, content: fullContent } : msg
                )
              );
            }
          }
        } catch (error) {
          if ((error as any).name !== "AbortError") {
            console.error("读取流错误:", error);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === aiMessageId
                  ? { ...msg, content: fullContent || "抱歉，我遇到了一些问题，请稍后再试。" }
                  : msg
              )
            );
          }
        } finally {
          setIsLoading(false);
          reader.releaseLock();
        }
      };

      readStream();

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
                    {isLoggedIn() ? (
                      <p>有什么问题可以随时问我～</p>
                    ) : (
                      <p className="text-amber-600">请先登录后再使用智能客服</p>
                    )}
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
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
          
          {/* 输入区域 */}
          <div className="p-4 border-t border-gray-200 flex-shrink-0">
            <div className="flex space-x-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入您的问题..."
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
