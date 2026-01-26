import { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Loader2, AlertTriangle } from "lucide-react";
import { useChat, useChatHistory } from "@/hooks/use-chat";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { Card } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

export default function Chat() {
  const [message, setMessage] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  
  const { data: history, isLoading: isLoadingHistory } = useChatHistory();
  const { mutate: sendMessage, isPending } = useChat();

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    sendMessage(message, {
      onError: (err) => {
        toast({
          title: "Error sending message",
          description: err.message,
          variant: "destructive",
        });
      },
      onSuccess: () => {
        setMessage("");
      }
    });
  };

  // Auto scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [history, isPending]);

  return (
    <div className="min-h-screen flex flex-col bg-muted/30">
      <Navigation />
      
      <main className="flex-1 container max-w-4xl mx-auto px-4 py-8 flex flex-col h-[calc(100vh-64px)]">
        <div className="mb-6">
           <h1 className="text-3xl font-bold font-display text-foreground">AI Medical Assistant</h1>
           <p className="text-muted-foreground">Ask questions about symptoms, medications, or general health.</p>
           
           <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg flex gap-3 text-sm text-yellow-800 dark:text-yellow-200">
             <AlertTriangle className="h-5 w-5 shrink-0" />
             <p>
               <strong>Disclaimer:</strong> This is an AI assistant, not a human doctor. 
               For emergencies, please visit your nearest hospital immediately. 
               Information provided is for educational purposes only.
             </p>
           </div>
        </div>

        <Card className="flex-1 flex flex-col overflow-hidden shadow-xl border-border/60 bg-white/80 dark:bg-card/80 backdrop-blur-sm">
          <ScrollArea className="flex-1 p-4 sm:p-6">
            <div className="space-y-6">
              {isLoadingHistory ? (
                 <div className="flex justify-center py-10">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                 </div>
              ) : history?.length === 0 ? (
                 <div className="text-center py-20 text-muted-foreground">
                    <Bot className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>No messages yet. Start a conversation!</p>
                 </div>
              ) : (
                history?.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-3 ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {msg.role === "assistant" && (
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Bot className="h-5 w-5 text-primary" />
                      </div>
                    )}
                    
                    <div
                      className={`max-w-[80%] px-4 py-3 rounded-2xl shadow-sm text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-primary text-white rounded-tr-sm"
                          : "bg-white dark:bg-muted border border-border/50 rounded-tl-sm"
                      }`}
                    >
                      {msg.content}
                    </div>

                    {msg.role === "user" && (
                      <div className="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center shrink-0">
                        <User className="h-5 w-5 text-secondary" />
                      </div>
                    )}
                  </div>
                ))
              )}
              
              {isPending && (
                <div className="flex gap-3 justify-start animate-pulse">
                   <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Bot className="h-5 w-5 text-primary" />
                   </div>
                   <div className="bg-white dark:bg-muted border border-border/50 px-4 py-3 rounded-2xl rounded-tl-sm">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                   </div>
                </div>
              )}
              <div ref={scrollRef} />
            </div>
          </ScrollArea>

          <div className="p-4 bg-muted/30 border-t">
            <form onSubmit={handleSend} className="flex gap-2">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your health concern here..."
                disabled={isPending}
                className="flex-1 bg-background rounded-full border-border/60 focus:ring-primary/20 px-6"
              />
              <Button 
                type="submit" 
                size="icon" 
                disabled={isPending || !message.trim()}
                className="rounded-full h-10 w-10 bg-primary hover:bg-primary/90 shadow-lg shadow-primary/25 transition-all"
              >
                {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </form>
          </div>
        </Card>
      </main>
      <Footer />
    </div>
  );
}
