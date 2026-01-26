import kenyaFlag from "@assets/kenya-kenya-flag_1769103297553.gif";
import { Heart, Facebook, Phone, Mail, MapPin } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";

export function Footer() {
  return (
    <footer className="bg-[#2A2D43] text-white border-t border-white/5 mt-auto">
      <div className="container max-w-7xl mx-auto px-6 py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          <div className="space-y-6">
            <h3 className="text-2xl font-black font-display tracking-tight">
              Elmed <span className="text-[#36D1DC]">Wellmind</span>
            </h3>
            <p className="text-white/70 leading-relaxed font-light">
              Nurturing minds and building resilience through professional guidance and community support tailored for Kenya.
            </p>
            <div className="flex items-center gap-3 bg-white/5 p-3 rounded-2xl w-fit">
                <img src={kenyaFlag} alt="Flag of Kenya" className="h-6 w-auto shadow-sm rounded-sm" />
                <span className="text-xs font-bold uppercase tracking-widest opacity-80">Proudly Kenyan</span>
            </div>
          </div>
          
          <div>
            <h4 className="font-bold mb-8 text-sm uppercase tracking-[0.2em] text-[#36D1DC]">Services</h4>
            <ul className="space-y-4 text-white/70">
              <li><a href="/chat" className="hover:text-white transition-colors">AI Health Doctor</a></li>
              <li><a href="/community" className="hover:text-white transition-colors">Community Forum</a></li>
              <li><a href="/about" className="hover:text-white transition-colors">Mental Wellness</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Maternal Care</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-8 text-sm uppercase tracking-[0.2em] text-[#36D1DC]">Quick Links</h4>
            <ul className="space-y-4 text-white/70">
              <li><a href="https://www.facebook.com/people/Elmed-Well-Mind/61585798993172/" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors flex items-center gap-2"><Facebook className="h-4 w-4" /> Facebook</a></li>
              <li><a href="https://wa.me/254759226354" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors flex items-center gap-2"><SiWhatsapp className="h-4 w-4" /> WhatsApp</a></li>
              <li><a href="mailto:elijahokware@gmail.com" className="hover:text-white transition-colors flex items-center gap-2"><Mail className="h-4 w-4" /> Email Us</a></li>
              <li><a href="tel:+254759226354" className="hover:text-white transition-colors flex items-center gap-2"><Phone className="h-4 w-4" /> Call Us</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-8 text-sm uppercase tracking-[0.2em] text-[#36D1DC]">Legal</h4>
            <ul className="space-y-4 text-white/70">
              <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Medical Disclaimer</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-white/10 mt-20 pt-10 flex flex-col md:flex-row justify-between items-center text-sm text-white/40 font-medium">
          <p>© {new Date().getFullYear()} Elmed Wellmind Solutions. All rights reserved.</p>
          <div className="flex items-center gap-2 mt-6 md:mt-0 bg-white/5 px-4 py-2 rounded-full">
            <span>Made with</span>
            <Heart className="h-4 w-4 text-[#FF6584] fill-[#FF6584] animate-pulse" />
            <span>for better mental health</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
