import { FC, useState } from "react";
import { Button } from "@/components/ui/button";
import PictopyLogo from "@/assets/PictoPy_Logo.png";
import MacLogo from "@/assets/mac-logo.png";
import WindowsLogo from "@/assets/windows-logo.svg";

const PictopyLanding: FC = () => {
  const [downloadStarted, setDownloadStarted] = useState<string | null>(null);

  const handleDownloadClick = (platform: string) => {
    setDownloadStarted(`Download for ${platform} started!`);
    setTimeout(() => setDownloadStarted(null), 3000);
  };

  return (
    <section className="relative w-full bg-white dark:bg-black overflow-hidden">

      {/* ===== Animated Background ===== */}
      <div className="absolute inset-0 -z-10">
        <svg
          className="w-full h-full"
          viewBox="0 0 1440 320"
          preserveAspectRatio="none"
        >
          <path
            fill="#00FF00"
            fillOpacity="0.08"
            d="M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V0H0Z"
          >
            <animate
              attributeName="d"
              dur="6s"
              repeatCount="indefinite"
              values="
              M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V0H0Z;
              M0,128L48,106.7C96,85,192,43,288,43C384,43,480,85,576,106.7C672,128,768,128,864,112C960,96,1056,64,1152,64C1248,64,1344,96,1392,128L1440,160V0H0Z;
              M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V0H0Z"
            />
          </path>
        </svg>
      </div>

      {/* ===== HERO SECTION ===== */}
      <div className="px-4 md:px-6 py-20 md:py-28 text-center">

        {/* Logo + Title */}
        <div className="flex justify-center items-center gap-4 mb-6">
          <img src={PictopyLogo} className="h-16 w-16" />
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-yellow-500 to-green-500 bg-clip-text text-transparent">
            PictoPy
          </h1>
        </div>

        {/* User-focused Tagline */}
        <p className="text-xl md:text-2xl text-gray-700 dark:text-gray-300 max-w-3xl mx-auto mb-10">
          Organize, view, and manage your photos effortlessly on Mac or Windows.
        </p>

        {/* ===== DOWNLOAD BUTTONS ===== */}
        <div className="flex flex-col sm:flex-row justify-center gap-6 mb-6">

          {/* Windows */}
          <Button
            onClick={() => handleDownloadClick("Windows")}
            className="h-14 px-10 rounded-full text-white text-lg bg-blue-600 hover:bg-blue-700 shadow-lg flex items-center gap-3"
          >
            <img src={WindowsLogo} className="h-6 w-6" />
            Download for Windows
          </Button>

          {/* Mac */}
          <Button
            onClick={() => handleDownloadClick("Mac")}
            className="h-14 px-10 rounded-full text-white text-lg bg-purple-600 hover:bg-purple-700 shadow-lg flex items-center gap-3"
          >
            <img src={MacLogo} className="h-6 w-6" />
            Download for Mac
          </Button>
        </div>

        {/* Version Text */}
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Version 1.0.0 | Released on February 2, 2025
        </p>
      </div>

      {/* ===== SCREENSHOTS ===== */}
      <div className="my-20 text-center">
        <h2 className="text-3xl font-bold mb-6">Screenshots</h2>
        <img
          src="/placeholder-screenshot.png"
          alt="PictoPy Screenshot"
          className="mx-auto rounded-lg shadow-lg w-3/4 md:w-1/2"
        />
      </div>

      {/* ===== DEMO VIDEO / GIF ===== */}
      <div className="my-20 text-center">
        <h2 className="text-3xl font-bold mb-6">See PictoPy in Action</h2>
        <video
          src="/demo.mp4"
          autoPlay
          loop
          muted
          className="mx-auto rounded-lg shadow-lg w-3/4 md:w-1/2"
        />
      </div>

      {/* ===== DOWNLOAD TOAST ===== */}
      {downloadStarted && (
        <div className="fixed top-16 right-6 bg-green-500 text-white px-6 py-3 rounded-lg shadow-xl animate-slideInRight">
          {downloadStarted}
        </div>
      )}
    </section>
  );
};

export default PictopyLanding;