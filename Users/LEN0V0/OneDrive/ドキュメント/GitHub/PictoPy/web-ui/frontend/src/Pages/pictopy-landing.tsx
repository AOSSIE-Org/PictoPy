import { FC, useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import PictopyLogo from "@/assets/PictoPy_Logo.png";
import MacLogo from "@/assets/mac-logo.png";
import WindowsLogo from "@/assets/windows-logo.svg";
import LinuxLogo from "@/assets/linux-logo.svg";

const PictopyLanding: FC = () => {
  const [downloadStarted, setDownloadStarted] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  // Animate on mount
  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleDownloadClick = (platform: string) => {
    setDownloadStarted(`Download for ${platform} started!`);
    setTimeout(() => {
      setDownloadStarted(null);
    }, 3000);
  };

  return (
    <section className="relative w-full py-16 md:py-32 bg-gradient-to-br from-slate-50 via-white to-green-50 dark:from-gray-900 dark:via-black dark:to-green-950 transition-all duration-500 overflow-hidden">
      {/* Enhanced Background Elements */}
      <div className="absolute inset-0 z-0">
        {/* Animated gradient orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-gradient-to-r from-green-400 to-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-gradient-to-r from-yellow-400 to-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse delay-1000"></div>
        <div className="absolute bottom-20 left-1/2 w-72 h-72 bg-gradient-to-r from-purple-400 to-green-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse delay-2000"></div>

        {/* Enhanced animated wave */}
        <svg
          className="absolute bottom-0 left-0 w-full h-64 md:h-80"
          viewBox="0 0 1440 320"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="waveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="0.1" />
              <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#eab308" stopOpacity="0.1" />
            </linearGradient>
          </defs>
          <path
            fill="url(#waveGradient)"
            d="M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V320H1392C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
          >
            <animate
              attributeName="d"
              dur="8s"
              repeatCount="indefinite"
              values="
                M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V320H1392C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z;
                M0,128L48,106.7C96,85,192,43,288,64C384,85,480,139,576,144C672,149,768,107,864,96C960,85,1056,107,1152,128C1248,149,1344,171,1392,192L1440,224V320H1392C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z;
                M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V320H1392C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
            />
          </path>
        </svg>

        {/* Floating particles */}
        <div className="absolute inset-0">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className={`absolute w-2 h-2 bg-green-400 rounded-full opacity-30 animate-float`}
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${i * 0.5}s`,
                animationDuration: `${3 + Math.random() * 2}s`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 md:px-6 relative z-10">
        <div className={`flex flex-col items-center text-center transition-all duration-1000 ${
          isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}>
          
          {/* Enhanced Logo and Title */}
          <div className="flex items-center justify-center gap-6 mb-8 group">
            <div className="relative">
              <div className="absolute -inset-2 bg-gradient-to-r from-green-400 to-blue-500 rounded-full opacity-75 group-hover:opacity-100 blur-sm transition-opacity duration-300"></div>
              <img
                src={PictopyLogo}
                alt="Pictopy Logo"
                className="relative h-20 w-20 md:h-24 md:w-24 object-contain transition-transform duration-300 group-hover:scale-110"
              />
            </div>
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-green-600 via-blue-600 to-yellow-500 transition-all duration-300 group-hover:from-yellow-500 group-hover:via-green-600 group-hover:to-blue-600 animate-gradient-x bg-300%">
              PictoPy
            </h1>
          </div>

          {/* Enhanced Subtitle with Stats */}
          <div className="mb-4">
            <p className="text-xl md:text-3xl lg:text-4xl font-medium text-gray-700 dark:text-gray-200 max-w-4xl mb-6 leading-relaxed">
              Organize your photos effortlessly with{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-blue-600 font-bold">
                AI-powered smart categorization
              </span>
            </p>
            
            {/* Stats Section */}
            <div className="flex flex-wrap justify-center gap-8 mb-8 text-sm md:text-base">
              <div className="flex flex-col items-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 transition-all duration-300 hover:scale-105 hover:bg-white/70 dark:hover:bg-gray-800/70">
                <span className="text-2xl md:text-3xl font-bold text-green-600 dark:text-green-400">150K+</span>
                <span className="text-gray-600 dark:text-gray-400 font-medium">Downloads</span>
              </div>
              <div className="flex flex-col items-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 transition-all duration-300 hover:scale-105 hover:bg-white/70 dark:hover:bg-gray-800/70">
                <span className="text-2xl md:text-3xl font-bold text-blue-600 dark:text-blue-400">4.9★</span>
                <span className="text-gray-600 dark:text-gray-400 font-medium">Rating</span>
              </div>
              <div className="flex flex-col items-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 transition-all duration-300 hover:scale-105 hover:bg-white/70 dark:hover:bg-gray-800/70">
                <span className="text-2xl md:text-3xl font-bold text-yellow-600 dark:text-yellow-400">100%</span>
                <span className="text-gray-600 dark:text-gray-400 font-medium">Free</span>
              </div>
            </div>
          </div>

          {/* Enhanced Download Buttons */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            {/* Mac Button */}
            <Button
              className="group relative bg-gradient-to-r from-gray-800 to-gray-900 hover:from-gray-900 hover:to-black dark:from-white dark:to-gray-100 dark:hover:from-gray-100 dark:hover:to-white text-white dark:text-black h-14 px-8 transition-all duration-300 border-2 border-transparent hover:border-gray-700 dark:hover:border-gray-300 transform hover:-translate-y-2 hover:shadow-2xl hover:shadow-gray-500/25 dark:hover:shadow-white/25 rounded-xl font-semibold text-lg overflow-hidden"
              size="lg"
              onClick={() => handleDownloadClick("Mac")}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              <img src={MacLogo} alt="Mac" className="h-8 w-8 mr-3 transition-transform duration-300 group-hover:scale-110" />
              <span className="relative z-10">Download for Mac</span>
            </Button>

            {/* Windows Button - Popular */}
            <Button
              className="group relative bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 dark:from-blue-500 dark:to-blue-600 dark:hover:from-blue-600 dark:hover:to-blue-700 text-white h-14 px-8 transition-all duration-300 border-2 border-blue-400 hover:border-blue-300 transform hover:-translate-y-2 hover:shadow-2xl hover:shadow-blue-500/25 rounded-xl font-semibold text-lg overflow-hidden scale-105"
              size="lg"
              onClick={() => handleDownloadClick("Windows")}
            >
              <div className="absolute -top-1 -right-1 bg-gradient-to-r from-orange-400 to-red-500 text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg animate-pulse">
                Popular
              </div>
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              <img src={WindowsLogo} alt="Windows" className="h-8 w-8 mr-3 transition-transform duration-300 group-hover:scale-110" />
              <span className="relative z-10">Download for Windows</span>
            </Button>

            {/* Linux Button */}
            <Button
              className="group relative bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 dark:from-yellow-400 dark:to-yellow-500 dark:hover:from-yellow-500 dark:hover:to-yellow-600 text-white h-14 px-8 transition-all duration-300 border-2 border-transparent hover:border-yellow-400 transform hover:-translate-y-2 hover:shadow-2xl hover:shadow-yellow-500/25 rounded-xl font-semibold text-lg overflow-hidden"
              size="lg"
              onClick={() => handleDownloadClick("Linux")}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              <img src={LinuxLogo} alt="Linux" className="h-9 w-9 mr-3 transition-transform duration-300 group-hover:scale-110" />
              <span className="relative z-10">Download for Linux(.deb)</span>
            </Button>
          </div>

          {/* Additional Info */}
          <p className="mt-8 text-sm md:text-base text-gray-500 dark:text-gray-400 max-w-2xl">
            Trusted by photographers and content creators worldwide. No subscription required.
          </p>
        </div>
      </div>

      {/* Enhanced Download Notification */}
      {downloadStarted && (
        <div className="fixed top-6 right-6 bg-gradient-to-r from-green-500 to-green-600 text-white py-4 px-6 rounded-xl shadow-2xl text-lg z-50 border border-green-400 backdrop-blur-sm animate-slideInRight">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
            {downloadStarted}
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes float {
          0%, 100% { 
            transform: translateY(0px) rotate(0deg); 
            opacity: 0.3;
          }
          50% { 
            transform: translateY(-20px) rotate(180deg); 
            opacity: 0.6;
          }
        }
        
        @keyframes gradient-x {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }
        
        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(100%);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        
        .animate-gradient-x {
          animation: gradient-x 3s ease infinite;
        }
        
        .animate-slideInRight {
          animation: slideInRight 0.3s ease-out;
        }
        
        .bg-300% {
          background-size: 300% 300%;
        }
      `}</style>
    </section>
  );
};

export default PictopyLanding;