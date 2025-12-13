import { FC, useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import PictopyLogo from "@/assets/PictoPy_Logo.png";
import MacLogo from "@/assets/mac-logo.png";
import WindowsLogo from "@/assets/windows-logo.svg";
import LinuxLogo from "@/assets/linux-logo.svg";

const PictopyLanding: FC = () => {
  // State for showing the notification
  const [downloadStarted, setDownloadStarted] = useState<string | null>(null);
  const [isLoadingReleases, setIsLoadingReleases] = useState(true);
  const [releaseError, setReleaseError] = useState<string | null>(null);
  const [releaseUrls, setReleaseUrls] = useState<{
    windows?: string;
    mac?: string;
    linux?: string;
  }>({});

  useEffect(() => {
    // Fetch the latest release information
    const fetchLatestRelease = async () => {
      try {
        setIsLoadingReleases(true);
        setReleaseError(null);
        const response = await fetch(
          "https://api.github.com/repos/AOSSIE-Org/PictoPy/releases/latest",
          {
            headers: {
              "X-GitHub-Api-Version": "2022-11-28",
            },
          }
        );

        if (!response.ok) {
          if (response.status === 403) {
            throw new Error(
              "GitHub API rate limit exceeded. Please try again later."
            );
          }
          throw new Error(
            `GitHub API returned ${response.status}: ${response.statusText}`
          );
        }

        const data = await response.json();
        const urls: { windows?: string; mac?: string; linux?: string } = {};

        // Prioritized asset selection
        data.assets.forEach((asset: any) => {
          const name = asset.name.toLowerCase();

          // Skip signature files
          if (name.endsWith(".sig")) {
            return;
          }

          // Windows - prefer .exe over .msi
          if (name.endsWith(".exe")) {
            urls.windows = asset.browser_download_url;
          } else if (name.endsWith(".msi") && !urls.windows) {
            urls.windows = asset.browser_download_url;
          }
          // Mac - prefer .dmg over .app.tar.gz
          else if (name.endsWith(".dmg")) {
            urls.mac = asset.browser_download_url;
          } else if (name.endsWith(".app.tar.gz") && !urls.mac) {
            urls.mac = asset.browser_download_url;
          }
          // Linux - prefer .appimage over .deb
          else if (name.endsWith(".appimage")) {
            urls.linux = asset.browser_download_url;
          } else if (name.endsWith(".deb") && !urls.linux) {
            urls.linux = asset.browser_download_url;
          }
        });

        setReleaseUrls(urls);
      } catch (error) {
        console.error("Failed to fetch latest release:", error);
        setReleaseError(
          error instanceof Error ? error.message : "Failed to fetch releases"
        );
      } finally {
        setIsLoadingReleases(false);
      }
    };

    fetchLatestRelease();
  }, []);

  // Function to handle button click and show the notification
  const handleDownloadClick = (platform: string) => {
    const url = releaseUrls[platform.toLowerCase() as keyof typeof releaseUrls];
    if (url) {
      window.open(url, "_blank");
      setDownloadStarted(`Download for ${platform} started!`);
      setTimeout(() => {
        setDownloadStarted(null);
      }, 3000);
    } else {
      setDownloadStarted(`Download link not available for ${platform}`);
      setTimeout(() => {
        setDownloadStarted(null);
      }, 3000);
    }
  };

  return (
    <section
      id="download-section"
      className="w-full py-12 md:py-24 bg-white dark:bg-black transition-colors duration-300 relative overflow-hidden"
    >
      {/* Background Animated SVG */}
      <div className="absolute inset-0 z-0">
        <svg
          className="w-full h-full"
          viewBox="0 0 1440 320"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="none"
        >
          <path
            fill="#00FF00"
            fillOpacity="0.1"
            d="M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V0H1392C1344,0,1248,0,1152,0C1056,0,960,0,864,0C768,0,672,0,576,0C480,0,384,0,288,0C192,0,96,0,48,0L0,0Z"
          >
            <animate
              attributeName="d"
              dur="5s"
              repeatCount="indefinite"
              values="
                M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V0H1392C1344,0,1248,0,1152,0C1056,0,960,0,864,0C768,0,672,0,576,0C480,0,384,0,288,0C192,0,96,0,48,0L0,0Z;
                M0,128L48,106.7C96,85,192,43,288,43C384,43,480,85,576,106.7C672,128,768,128,864,112C960,96,1056,64,1152,64C1248,64,1344,96,1392,128L1440,160V0H1392C1344,0,1248,0,1152,0C1056,0,960,0,864,0C768,0,672,0,576,0C480,0,384,0,288,0C192,0,96,0,48,0L0,0Z;
                M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V0H1392C1344,0,1248,0,1152,0C1056,0,960,0,864,0C768,0,672,0,576,0C480,0,384,0,288,0C192,0,96,0,48,0L0,0Z"
            />
          </path>
        </svg>
      </div>

      {/* Content */}
      <div className="px-4 md:px-6 relative z-10 ">
        <div className="flex flex-col items-center text-center">
          {/* Heading with Gradient Text and Logo */}
          <div className="flex items-center justify-center gap-4 mb-4">
            <img
              src={PictopyLogo}
              alt="Pictopy Logo"
              className="h-16 w-16 object-contain"
            />
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-yellow-500 to-green-500 transition-all duration-300">
              PictoPy
            </h1>
          </div>

          {/* Subheading */}
          <p className="text-xl md:text-2xl text-green-700 dark:text-yellow-300 max-w-3xl mb-8 transition-colors duration-300">
            Organize your photos effortlessly. Available for Mac, Windows, and
            Linux.
          </p>

          {/* Download Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              className="bg-black text-white hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-gray-200 h-12 px-8 transition-all duration-300 
                         border-2 border-transparent hover:border-black dark:hover:border-white 
                         transform hover:-translate-y-1 hover:shadow-lg"
              size="lg"
              onClick={() => handleDownloadClick("Mac")}
              disabled={isLoadingReleases || !!releaseError || !releaseUrls.mac}
            >
              <img src={MacLogo} alt="Mac" className="h-7 w-7 mr-2" />
              Download for Mac
            </Button>
            <Button
              className="bg-black text-white hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-gray-200 h-12 px-8 transition-all duration-300 
                         border-2 border-transparent hover:border-black dark:hover:border-white 
                         transform hover:-translate-y-1 hover:shadow-lg"
              size="lg"
              variant="outline"
              onClick={() => handleDownloadClick("Windows")}
              disabled={isLoadingReleases || !!releaseError || !releaseUrls.windows}
            >
              <img src={WindowsLogo} alt="Windows" className="h-7 w-7 mr-2" />
              Download for Windows
            </Button>
            <Button
              className="bg-black text-white hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-gray-200 h-12 px-8 transition-all duration-300 
                         border-2 border-transparent hover:border-black dark:hover:border-white 
                         transform hover:-translate-y-1 hover:shadow-lg"
              size="lg"
              variant="outline"
              onClick={() => handleDownloadClick("Linux")}
              disabled={isLoadingReleases || !!releaseError || !releaseUrls.linux}
            >
              <img src={LinuxLogo} alt="Linux" className="h-9 w-9 mr-2" />
              Download for Linux(.deb)
            </Button>
          </div>

          {/* Loading Indicator */}
          {isLoadingReleases && (
            <div className="mt-4 text-center text-slate-600 dark:text-slate-400">
              Loading latest releases...
            </div>
          )}

          {/* Download Notification (Popup) */}
          {downloadStarted && (
            <div className="fixed top-16 right-4 md:right-8 bg-green-500 text-white py-3 px-6 rounded-lg shadow-xl text-lg z-50 opacity-0 animate-slideInRight">
              {downloadStarted}
            </div>
          )}

          {/* Error Notification */}
          {releaseError && (
            <div className="fixed top-16 right-4 md:right-8 bg-red-500 text-white py-3 px-6 rounded-lg shadow-xl text-lg z-50">
              {releaseError}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default PictopyLanding;
