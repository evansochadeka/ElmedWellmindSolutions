import { Link, useLocation } from "wouter";
import { MessageSquare, Users, Home, Info, Menu, X, Phone, Mail, Facebook, Heart } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import wellmedLogo from "@assets/wellmed_1769103297554.jpg";

export function Navigation() {
  const [location] = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { href: "/", label: "Home", icon: Home },
    { href: "/chat", label: "AI Doctor", icon: MessageSquare },
    { href: "/community", label: "Community", icon: Users },
    { href: "/about", label: "About", icon: Info },
  ];

  const isActive = (path: string) => location === path;

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-20 items-center justify-between px-4 sm:px-8 max-w-7xl mx-auto">
        <Link href="/" className="flex items-center gap-2 transition-opacity hover:opacity-80">
            <img src={wellmedLogo} alt="WellMed Logo" className="h-12 w-12 rounded-full object-cover shadow-sm" />
            <div className="flex flex-col">
              <span className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent hidden sm:inline-block leading-tight">
                  Elmed Wellmind
              </span>
              <span className="text-[10px] text-primary font-medium tracking-wider hidden sm:inline-block">SOLUTIONS</span>
            </div>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          <div className="flex items-center gap-6 mr-4 border-r pr-6 border-border/50">
            {navItems.map((item) => (
              <Link key={item.href} href={item.href} className={`
                  flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary
                  ${isActive(item.href) ? "text-primary font-semibold" : "text-muted-foreground"}
                `}>
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            ))}
          </div>
          
          <div className="flex items-center gap-3">
             <Button variant="default" className="bg-gradient-to-r from-[#6C63FF] to-[#36D1DC] hover:scale-105 transition-transform text-white shadow-lg shadow-primary/20 rounded-full px-6">
                Get Started
              </Button>
              <Button variant="outline" className="border-primary/20 text-primary hover:bg-primary/5 rounded-full px-6 gap-2" asChild>
                <a href="https://www.paypal.com/donate" target="_blank" rel="noopener noreferrer">
                  <Heart className="h-4 w-4 fill-primary/10" />
                  Donate
                </a>
              </Button>
          </div>
        </div>

        {/* Mobile Menu Button */}
        <button className="md:hidden p-2" onClick={() => setIsOpen(!isOpen)}>
          {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile Nav */}
      {isOpen && (
        <div className="md:hidden border-b bg-background p-6 animate-in slide-in-from-top-2">
          <div className="flex flex-col space-y-4">
            {navItems.map((item) => (
              <Link 
                key={item.href} 
                href={item.href} 
                onClick={() => setIsOpen(false)}
                className={`
                  flex items-center gap-3 p-3 rounded-xl text-sm font-medium transition-colors
                  ${isActive(item.href) ? "bg-primary/10 text-primary" : "hover:bg-muted text-foreground"}
                `}
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </Link>
            ))}
            <hr className="border-border/50 my-2" />
            <Button className="w-full bg-primary hover:bg-primary/90 text-white rounded-xl py-6">
                Get Started
            </Button>
            <Button variant="outline" className="w-full border-primary/20 text-primary rounded-xl py-6 gap-2" asChild>
                <a href="https://www.paypal.com/donate" target="_blank" rel="noopener noreferrer">
                  <Heart className="h-4 w-4" />
                  Donate
                </a>
            </Button>
          </div>
        </div>
      )}
    </nav>
  );
}
