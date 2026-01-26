import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

// Unsplash image for Medical Team/About
const aboutImage = "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?q=80&w=1920&auto=format&fit=crop";

export default function About() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navigation />
      
      <main className="flex-1">
        <section className="relative h-[40vh] min-h-[400px] flex items-center justify-center overflow-hidden">
            <div className="absolute inset-0 bg-black/60 z-10" />
            <div 
                className="absolute inset-0 bg-cover bg-center"
                style={{ backgroundImage: `url(${aboutImage})` }}
            />
            <div className="relative z-20 container max-w-4xl text-center px-4">
                <h1 className="text-4xl md:text-5xl font-bold font-display text-white mb-6">Bridging the Healthcare Gap</h1>
                <p className="text-xl text-white/90 max-w-2xl mx-auto">
                    WellMed Kenya leverages technology to make quality health information accessible to everyone, everywhere.
                </p>
            </div>
        </section>

        <section className="py-20 container max-w-4xl mx-auto px-4">
            <div className="space-y-12">
                <div>
                    <h2 className="text-3xl font-bold font-display text-primary mb-6">Our Mission</h2>
                    <p className="text-lg text-muted-foreground leading-relaxed">
                        To democratize access to healthcare information in Kenya by providing a reliable, 
                        AI-powered platform that understands local context, languages, and health challenges. 
                        We believe that information is the first step towards better health outcomes.
                    </p>
                </div>
                
                <Separator />
                
                <div className="grid md:grid-cols-2 gap-12">
                    <div>
                        <h3 className="text-xl font-bold mb-4 text-foreground">For Patients</h3>
                        <ul className="space-y-3 text-muted-foreground">
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-secondary" />
                                Instant answers to health queries
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-secondary" />
                                Community support and shared experiences
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-secondary" />
                                Privacy and anonymity guaranteed
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h3 className="text-xl font-bold mb-4 text-foreground">For Healthcare</h3>
                        <ul className="space-y-3 text-muted-foreground">
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-primary" />
                                Reducing burden on primary care facilities
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-primary" />
                                Data-driven insights on community health
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-primary" />
                                Promotion of preventative care
                            </li>
                        </ul>
                    </div>
                </div>

                <Card className="bg-primary/5 border-primary/10 p-8 rounded-2xl text-center">
                    <h2 className="text-2xl font-bold font-display mb-4">Join Our Journey</h2>
                    <p className="text-muted-foreground mb-6">
                        We are constantly evolving to serve you better. Your feedback shapes the future of WellMed.
                    </p>
                    <p className="font-medium text-primary">contact@wellmed.co.ke</p>
                </Card>
            </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
