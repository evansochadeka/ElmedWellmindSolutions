import { useState } from "react";
import { Plus, MessageCircle, ThumbsUp, CheckCircle2, Search, Filter } from "lucide-react";
import { useConcerns, useCreateConcern, useCategories, useUpvoteConcern } from "@/hooks/use-concerns";
import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertConcernSchema, type InsertConcern, CATEGORIES } from "@shared/routes";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Card } from "@/components/ui/card";
import { formatDistanceToNow } from "date-fns";

export default function Community() {
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const [search, setSearch] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  
  // Cast category to match the type expected by useConcerns
  const categoryFilter = selectedCategory && selectedCategory !== "All" ? selectedCategory as typeof CATEGORIES[number] : undefined;
  
  const { data: concerns, isLoading } = useConcerns({ 
    category: categoryFilter, 
    search: search 
  });
  
  const { data: categories } = useCategories();

  return (
    <div className="min-h-screen flex flex-col bg-muted/30">
      <Navigation />
      
      <main className="flex-1 container max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold font-display text-foreground mb-2">Community Forum</h1>
            <p className="text-muted-foreground">Share concerns and find support from the community.</p>
          </div>
          
          <CreateConcernDialog open={isCreateOpen} onOpenChange={setIsCreateOpen} />
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-card rounded-xl p-4 shadow-sm border border-border/60 mb-8 flex flex-col md:flex-row gap-4 items-center">
            <div className="relative w-full md:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input 
                    placeholder="Search concerns..." 
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 bg-muted/30 border-transparent focus:bg-background transition-colors"
                />
            </div>
            
            <div className="w-full md:w-48">
                <Select value={selectedCategory || "All"} onValueChange={setSelectedCategory}>
                    <SelectTrigger className="w-full bg-muted/30 border-transparent focus:bg-background">
                        <div className="flex items-center gap-2">
                            <Filter className="h-4 w-4 text-muted-foreground" />
                            <SelectValue placeholder="Category" />
                        </div>
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="All">All Categories</SelectItem>
                        {categories?.map((cat) => (
                            <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
             // Skeletons
             Array.from({ length: 6 }).map((_, i) => (
               <div key={i} className="h-64 rounded-2xl bg-muted/20 animate-pulse border border-border/50" />
             ))
          ) : concerns?.length === 0 ? (
             <div className="col-span-full py-16 text-center text-muted-foreground">
                <MessageCircle className="h-16 w-16 mx-auto mb-4 opacity-20" />
                <p className="text-lg">No concerns found matching your criteria.</p>
             </div>
          ) : (
            concerns?.map((concern) => (
              <ConcernCard key={concern.id} concern={concern} />
            ))
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

function ConcernCard({ concern }: { concern: any }) {
    const { mutate: upvote } = useUpvoteConcern();
    
    return (
        <Card className="flex flex-col h-full hover:shadow-lg transition-all duration-300 border-border/60 bg-white dark:bg-card">
            <div className="p-6 flex-1">
                <div className="flex justify-between items-start mb-4">
                    <Badge variant={concern.status === 'resolved' ? 'default' : 'secondary'} className={`
                        ${concern.status === 'resolved' ? 'bg-green-100 text-green-700 hover:bg-green-100' : 'bg-secondary/10 text-secondary hover:bg-secondary/10'}
                    `}>
                        {concern.status === 'resolved' ? <CheckCircle2 className="w-3 h-3 mr-1" /> : null}
                        {concern.status === 'resolved' ? 'Resolved' : 'Open'}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                        {concern.createdAt ? formatDistanceToNow(new Date(concern.createdAt), { addSuffix: true }) : ''}
                    </span>
                </div>
                
                <h3 className="text-xl font-bold font-display mb-2 line-clamp-2">{concern.title}</h3>
                <Badge variant="outline" className="mb-4 text-xs font-normal text-muted-foreground">{concern.category}</Badge>
                
                <p className="text-muted-foreground text-sm line-clamp-3 mb-4">
                    {concern.content}
                </p>

                {concern.response && (
                    <div className="bg-primary/5 rounded-lg p-3 text-sm mt-4 border border-primary/10">
                        <p className="font-semibold text-primary text-xs mb-1">Doctor's Response:</p>
                        <p className="line-clamp-2 text-foreground/80">{concern.response}</p>
                    </div>
                )}
            </div>
            
            <div className="p-4 border-t bg-muted/20 flex justify-between items-center">
                <Button 
                    variant="ghost" 
                    size="sm" 
                    className="text-muted-foreground hover:text-primary gap-2"
                    onClick={() => upvote(concern.id)}
                >
                    <ThumbsUp className="h-4 w-4" />
                    <span>{concern.upvotes || 0}</span>
                </Button>
                
                <Button variant="link" size="sm" className="text-primary font-medium">
                    Read More
                </Button>
            </div>
        </Card>
    );
}

function CreateConcernDialog({ open, onOpenChange }: { open: boolean, onOpenChange: (open: boolean) => void }) {
    const { toast } = useToast();
    const { mutate: createConcern, isPending } = useCreateConcern();
    const { data: categories } = useCategories();
    
    const form = useForm<InsertConcern>({
        resolver: zodResolver(insertConcernSchema),
        defaultValues: {
            title: "",
            content: "",
            category: "General Health", // default
        }
    });

    const onSubmit = (data: InsertConcern) => {
        createConcern(data, {
            onSuccess: () => {
                toast({ title: "Concern Posted", description: "Your concern has been shared with the community." });
                onOpenChange(false);
                form.reset();
            },
            onError: (err) => {
                toast({ title: "Error", description: err.message, variant: "destructive" });
            }
        });
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogTrigger asChild>
                <Button className="bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/20">
                    <Plus className="mr-2 h-4 w-4" /> Post Concern
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle className="font-display text-2xl">Post a Concern</DialogTitle>
                </DialogHeader>
                
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 py-4">
                        <FormField
                            control={form.control}
                            name="title"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Title</FormLabel>
                                    <FormControl>
                                        <Input placeholder="Brief summary of your concern" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        
                        <FormField
                            control={form.control}
                            name="category"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Category</FormLabel>
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select a category" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {categories?.map((cat) => (
                                                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        
                        <FormField
                            control={form.control}
                            name="content"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Details</FormLabel>
                                    <FormControl>
                                        <Textarea 
                                            placeholder="Describe your symptoms or question in detail..." 
                                            className="min-h-[120px]"
                                            {...field} 
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        
                        <div className="flex justify-end pt-4">
                            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} className="mr-2">Cancel</Button>
                            <Button type="submit" disabled={isPending}>
                                {isPending ? "Posting..." : "Post Concern"}
                            </Button>
                        </div>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
