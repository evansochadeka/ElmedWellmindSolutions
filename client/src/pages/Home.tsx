import { Link } from "wouter";
import { 
  ArrowRight, MessageSquare, Users, ShieldCheck, Heart, Brain, Baby, Apple, Activity, 
  Phone, Mail, Facebook, Send, DollarSign
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SiWhatsapp } from "react-icons/si";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-[#F8F9FF] font-sans overflow-x-hidden">
      <Navigation />
      
      {/* Hero Section */}
      <section className="relative min-h-[95vh] flex items-center overflow-hidden">
        {/* Hero Background Elements */}
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-br from-[#2A2D43]/80 via-[#2A2D43]/60 to-[#2A2D43]/80 z-10" />
          <img 
            src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80" 
            alt="Medical Professional" 
            className="w-full h-full object-cover scale-105 animate-pulse-slow"
          />
        </div>

        <div className="container relative z-20 max-w-[1300px] mx-auto px-6">
          <div className="max-w-[850px] text-white">
            <Badge className="mb-6 bg-white/20 backdrop-blur-md text-white border-white/30 px-4 py-1 text-sm rounded-full">
              Trustworthy Mental Wellness in Kenya
            </Badge>
            <h1 className="text-6xl md:text-8xl font-black font-display mb-6 leading-[1.1] drop-shadow-2xl">
              Nurturing <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#6C63FF] via-[#36D1DC] to-[#6C63FF] animate-gradient-x">
                Resilient Minds
              </span>
            </h1>
            <p className="text-xl md:text-2xl opacity-90 mb-10 max-w-2xl font-light leading-relaxed">
              Expert mental wellness guidance tailored for our local context. 
              Join a supportive community where your mental health matters most.
            </p>
            <div className="flex flex-wrap gap-6">
              <Link href="/chat">
                <Button size="lg" className="rounded-full bg-gradient-to-r from-[#6C63FF] to-[#36D1DC] hover:scale-110 active:scale-95 transition-all px-12 py-8 text-xl font-black shadow-2xl shadow-primary/40 group">
                  CONSULT AI <ArrowRight className="ml-2 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Link href="/community">
                <Button variant="outline" size="lg" className="rounded-full bg-white/10 backdrop-blur-xl border-2 border-white/40 text-white hover:bg-white/20 transition-all px-12 py-8 text-xl font-black shadow-xl">
                  FORUM
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Floating Contact Icons */}
        <div className="absolute right-8 bottom-32 z-30 flex flex-col gap-4">
          <ContactIcon 
            href="https://wa.me/254759226354" 
            icon={SiWhatsapp} 
            color="bg-[#25D366]" 
            label="WhatsApp" 
          />
          <ContactIcon 
            href="tel:+254759226354" 
            icon={Phone} 
            color="bg-[#36D1DC]" 
            label="Call Us" 
          />
        </div>
      </section>

      {/* Services Section */}
      <section className="py-32 bg-white relative">
        <div className="container max-w-[1300px] mx-auto px-6 text-center">
          <div className="mb-20">
            <h2 className="text-5xl md:text-6xl font-black mb-6 font-display">
              Why Choose <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#6C63FF] to-[#36D1DC]">Elmed?</span>
            </h2>
            <div className="h-1.5 w-24 bg-gradient-to-r from-[#6C63FF] to-[#36D1DC] mx-auto rounded-full mb-8" />
            <p className="text-muted-foreground text-2xl max-w-3xl mx-auto leading-relaxed font-light">
              We merge advanced AI technology with deep local medical expertise to deliver compassionate wellness solutions.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-10">
            <ServiceCard 
              icon={Brain}
              title="Mental Wellness"
              description="Confidential support for anxiety and depression tailored specifically for Kenyans."
            />
            <ServiceCard 
              icon={Activity}
              title="AI Consultations"
              description="Get instant medical guidance based on local health protocols, 24/7."
            />
            <ServiceCard 
              icon={Users}
              title="Communal Healing"
              description="Safe spaces to share, learn, and grow together as a resilient community."
            />
          </div>
        </div>
      </section>

      {/* Donation Section */}
      <section className="py-24 bg-[#F0F2FF] border-y border-primary/10">
        <div className="container max-w-[1300px] mx-auto px-6">
          <div className="bg-white rounded-[3rem] p-10 md:p-20 shadow-2xl flex flex-col lg:flex-row items-center gap-16 border border-primary/5">
            <div className="flex-1 text-center lg:text-left">
              <Badge className="bg-primary/10 text-primary border-primary/20 mb-6 px-4 py-1 text-sm rounded-full font-bold">
                Support Our Mission
              </Badge>
              <h2 className="text-5xl md:text-6xl font-black mb-8 font-display leading-tight">
                Empower <span className="text-[#6C63FF]">Better Health</span> For All
              </h2>
              <p className="text-xl text-muted-foreground mb-10 leading-relaxed max-w-xl">
                Your generous contribution helps us provide free mental wellness guidance and maintain our support systems for those in need across Kenya.
              </p>
              <div className="flex flex-wrap justify-center lg:justify-start gap-4">
                <Button size="lg" className="rounded-full bg-[#6C63FF] px-10 py-8 text-xl font-bold shadow-xl shadow-primary/20 hover:scale-105 transition-transform">
                  <Heart className="mr-2 h-6 w-6 fill-white" /> DONATE NOW
                </Button>
                <div className="flex items-center gap-4 p-4 rounded-3xl bg-primary/5 border border-primary/10">
                  <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center shadow-sm">
                    <span className="text-primary font-black">M</span>
                  </div>
                  <div className="text-left">
                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Pay via M-Pesa</p>
                    <p className="text-lg font-black text-primary">+254 759 226 354</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="lg:w-1/3 w-full">
              <Card className="rounded-[2.5rem] border-primary/10 bg-[#F8F9FF] shadow-inner overflow-hidden">
                <CardContent className="p-8 space-y-6">
                  <div className="text-center">
                    <p className="text-sm font-bold text-muted-foreground mb-2">SELECT AMOUNT</p>
                    <div className="flex justify-between gap-2">
                      {['$10', '$25', '$50', 'Custom'].map((amt) => (
                        <Button key={amt} variant="outline" className={`flex-1 rounded-2xl border-2 ${amt === '$25' ? 'border-primary bg-primary/5 text-primary' : 'border-border'}`}>
                          {amt}
                        </Button>
                      ))}
                    </div>
                  </div>
                  <Button variant="outline" className="w-full rounded-2xl py-7 text-lg font-bold border-2 border-[#0070BA] text-[#0070BA] hover:bg-[#0070BA]/5">
                    Pay with PayPal
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Community Section */}
      <section className="py-32 bg-gradient-to-br from-[#6C63FF] to-[#36D1DC] text-white relative">
        <div className="container max-w-[1300px] mx-auto px-6 flex flex-col lg:flex-row gap-20 items-center">
          <div className="flex-1">
            <h2 className="text-5xl md:text-7xl font-black mb-8 font-display leading-tight">
              A Community <br /> Built on <span className="underline decoration-[#FF6584] decoration-8 underline-offset-8">Trust</span>
            </h2>
            <p className="text-2xl opacity-90 mb-12 leading-relaxed font-light">
              Don't navigate your health journey alone. Post your concerns, get advice, and find support in real-time.
            </p>
            <Link href="/community">
              <Button size="lg" className="rounded-full bg-white text-[#6C63FF] px-12 py-8 text-xl font-black hover:scale-105 transition-transform shadow-2xl">
                POST A CONCERN
              </Button>
            </Link>
          </div>
          <div className="flex-1 w-full max-w-xl">
             <Card className="rounded-[3rem] bg-white/10 backdrop-blur-2xl border-white/20 shadow-[0_30px_60px_rgba(0,0,0,0.3)] text-white overflow-hidden">
                <CardContent className="p-10">
                   <div className="flex justify-between items-center mb-10">
                      <div className="flex items-center gap-4">
                         <div className="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center">
                            <Users className="h-7 w-7" />
                         </div>
                         <h3 className="text-3xl font-black">Live Forum</h3>
                      </div>
                      <Badge className="bg-[#FF6584] text-white px-4 py-1 animate-pulse">Live</Badge>
                   </div>
                   <div className="space-y-8">
                      <CommunityPostPreview 
                        title="Dealing with burnout as a parent"
                        author="Jane M."
                        upvotes={42}
                        category="Mental Health"
                      />
                      <CommunityPostPreview 
                        title="Best local snacks for active toddlers"
                        author="Kiprono T."
                        upvotes={18}
                        category="Nutrition"
                      />
                   </div>
                </CardContent>
             </Card>
          </div>
        </div>
      </section>

      {/* Final Contact Section */}
      <section className="py-32 bg-white overflow-hidden">
        <div className="container max-w-[1300px] mx-auto px-6">
           <div className="grid lg:grid-cols-2 gap-20 items-center">
              <div>
                 <Badge className="mb-6 bg-primary/10 text-primary border-primary/20 px-4 py-1 text-sm rounded-full font-bold">
                    Get in Touch
                 </Badge>
                 <h2 className="text-5xl md:text-6xl font-black mb-10 font-display">
                    Connect With <br /> <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#6C63FF] to-[#36D1DC]">Elmed Experts</span>
                 </h2>
                 <div className="space-y-8">
                    <ContactDetail 
                      icon={Phone} 
                      title="Call or WhatsApp" 
                      detail="+254 759 226 354"
                      href="tel:+254759226354"
                    />
                    <ContactDetail 
                      icon={Mail} 
                      title="Email Us" 
                      detail="elijahokware@gmail.com"
                      href="mailto:elijahokware@gmail.com"
                    />
                    <ContactDetail 
                      icon={Facebook} 
                      title="Follow Us" 
                      detail="Elmed Well Mind"
                      href="https://www.facebook.com/people/Elmed-Well-Mind/61585798993172/"
                    />
                 </div>
              </div>
              <div className="relative">
                 <div className="absolute -inset-10 bg-gradient-to-br from-[#6C63FF]/10 to-[#36D1DC]/10 rounded-full blur-3xl -z-10" />
                 <Card className="rounded-[3rem] p-12 shadow-2xl border-primary/5 bg-white relative z-10">
                    <h3 className="text-3xl font-black mb-8">Quick Message</h3>
                    <div className="space-y-6">
                       <Input placeholder="Full Name" className="rounded-2xl py-7 bg-[#F8F9FF] border-transparent focus:border-primary/30" />
                       <Input placeholder="Email Address" className="rounded-2xl py-7 bg-[#F8F9FF] border-transparent focus:border-primary/30" />
                       <Textarea placeholder="How can we help you today?" className="rounded-2xl min-h-[150px] bg-[#F8F9FF] border-transparent focus:border-primary/30" />
                       <Button className="w-full rounded-2xl py-8 text-xl font-bold bg-gradient-to-r from-[#6C63FF] to-[#36D1DC] shadow-xl shadow-primary/20 hover:scale-[1.02] transition-transform">
                          SEND MESSAGE <Send className="ml-2 h-5 w-5" />
                       </Button>
                    </div>
                 </Card>
              </div>
           </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

function ServiceCard({ icon: Icon, title, description }: any) {
  return (
    <Card className="p-10 rounded-[2.5rem] border-transparent hover:border-primary/10 hover:shadow-[0_40px_80px_-20px_rgba(108,99,255,0.15)] transition-all duration-700 group relative overflow-hidden bg-[#FBFBFF]">
      <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-[#6C63FF] to-[#36D1DC] scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500" />
      <div className="mb-8 relative">
        <div className="w-20 h-20 rounded-[1.5rem] bg-white flex items-center justify-center group-hover:rotate-[10deg] transition-all duration-500 shadow-sm border border-primary/5">
          <Icon className="h-10 w-10 text-[#6C63FF]" />
        </div>
      </div>
      <h3 className="text-3xl font-black mb-4 font-display group-hover:text-[#6C63FF] transition-colors">{title}</h3>
      <p className="text-muted-foreground leading-relaxed text-xl font-light">
        {description}
      </p>
    </Card>
  );
}

function ContactIcon({ href, icon: Icon, color, label }: any) {
  return (
    <a 
      href={href} 
      target="_blank" 
      rel="noopener noreferrer" 
      className={`group relative w-16 h-16 rounded-2xl ${color} text-white flex items-center justify-center shadow-2xl hover:scale-110 active:scale-90 transition-all z-50`}
    >
      <Icon className="h-8 w-8" />
      <span className="absolute right-full mr-4 bg-white text-dark px-3 py-1.5 rounded-xl text-sm font-bold shadow-xl opacity-0 translate-x-4 pointer-events-none group-hover:opacity-100 group-hover:translate-x-0 transition-all whitespace-nowrap">
        {label}
      </span>
    </a>
  );
}

function ContactDetail({ icon: Icon, title, detail, href }: any) {
  return (
    <a href={href} className="flex items-center gap-6 group">
      <div className="w-16 h-16 rounded-2xl bg-[#F8F9FF] flex items-center justify-center text-[#6C63FF] shadow-sm group-hover:bg-[#6C63FF] group-hover:text-white transition-all">
        <Icon className="h-7 w-7" />
      </div>
      <div>
        <p className="text-sm font-bold text-muted-foreground uppercase tracking-widest mb-1">{title}</p>
        <p className="text-2xl font-black group-hover:text-[#6C63FF] transition-colors">{detail}</p>
      </div>
    </a>
  );
}

function CommunityPostPreview({ title, author, upvotes, category }: any) {
  return (
    <div className="p-6 bg-white/5 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors cursor-pointer group">
      <Badge className="mb-4 bg-white/20 text-white border-0">{category}</Badge>
      <p className="text-xl font-bold mb-4 group-hover:text-[#36D1DC] transition-colors leading-tight">{title}</p>
      <div className="flex justify-between items-center opacity-80">
        <span className="text-sm font-medium">By {author}</span>
        <div className="flex items-center gap-2">
          <Heart className="h-4 w-4 fill-white" />
          <span className="text-sm font-bold">{upvotes}</span>
        </div>
      </div>
    </div>
  );
}
