import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { ThemeSelector } from "@/components/ThemeToggle";
import { Search, Mic } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";
import { selectAvatar, selectName } from "@/features/onboardingSelectors";
import { clearSearch } from "@/features/searchSlice";
import { convertFileSrc } from "@tauri-apps/api/core";
import { FaceSearchDialog } from "@/components/Dialog/FaceSearchDialog";

// Error Dialog
const ErrorDialog = ({ message, onClose }: { message: string; onClose: () => void }) => (
  <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
    <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl p-6 max-w-sm w-full text-center border border-white/20 dark:border-neutral-700/50 relative">
      <h2 className="text-xl font-semibold text-red-600 mb-2">Something went wrong</h2>
      <p className="text-sm text-neutral-600 dark:text-neutral-300">{message}</p>
      <button
        onClick={onClose}
        className="absolute top-2 right-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 font-bold"
      >
        ✕
      </button>
    </div>
  </div>
);

export function Navbar() {
  const userName = useSelector(selectName);
  const userAvatar = useSelector(selectAvatar);
  const searchState = useSelector((state: any) => state.search);
  const dispatch = useDispatch();

  const isSearchActive = searchState.active;
  const queryImage = searchState.queryImage;

  const routeMap: Record<string, string> = {
    home: "/",
    albums: "/albums",
    videos: "/videos",
    settings: "/settings",
    "ai-tagging": "/ai-tagging",
    memories: "/memories",
  };

  const suggestionKeys = ["home", "albums", "videos", "settings", "ai-tagging", "memories"];

  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [voiceText, setVoiceText] = useState("Listening...");
  const [error, setError] = useState<string | null>(null);

  const filtered = query
    ? suggestionKeys.filter((s) =>
        s.toLowerCase().includes(query.toLowerCase().replace(/\s+/g, "-"))
      )
    : [];

  const goToPage = (label: string) => {
    const key = label.trim().toLowerCase().replace(/\s+/g, "-");

    if (routeMap[key]) {
      window.location.assign(routeMap[key]); 
    } else {
      setError(`The page "${label}" does not exist.`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!filtered.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1) % filtered.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((prev) => (prev <= 0 ? filtered.length - 1 : prev - 1));
    } else if (e.key === "Enter") {
      if (activeIndex >= 0 && activeIndex < filtered.length) {
        goToPage(filtered[activeIndex]);
        setActiveIndex(-1);
      }
    }
  };

  useEffect(() => {
    setActiveIndex(-1);
  }, [query]);

 
  const startListening = () => {
    const SR =
      (window as any).webkitSpeechRecognition ||
      (window as any).SpeechRecognition;

    if (!SR) {
      setError("Speech recognition is not supported in your browser.");
      return;
    }

    const recog = new SR();
    recog.lang = "en-US";
    recog.interimResults = false;

    recog.onstart = () => {
      setVoiceOpen(true);
      setVoiceText("Listening...");
    };

    recog.onresult = (e: any) => {
      const spoken = e.results[0][0].transcript;
      setVoiceText(spoken);

      const found = suggestionKeys.find((k) =>
        spoken.toLowerCase().replace(/\s+/g, "-").includes(k)
      );

      if (found) {
        goToPage(found);
      } else {
        setError(`No matching page found for "${spoken}".`);
      }

      setTimeout(() => setVoiceOpen(false), 1200);
    };

    recog.onerror = (event: any) => {
      const msg =
        event.error === "no-speech"
          ? "No speech detected. Try again."
          : "Couldn't understand. Try again.";
      setVoiceText(msg);
      setTimeout(() => setVoiceOpen(false), 1200);
    };

    recog.start();

    return () => {
      recog.stop();
    };
  };

  return (
    <div className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b bg-white/70 dark:bg-black/40 backdrop-blur px-4">
      {/* LEFT */}
      <div className="flex w-[256px] items-center gap-2">
        <img src="/128x128.png" width={32} height={32} alt="PictoPy Logo" />
        <span className="text-xl font-bold">PictoPy</span>
      </div>

      {/* CENTER */}
      <div className="relative mx-auto flex max-w-xl flex-1 justify-center px-4">
        <div className="flex w-full items-center gap-2 rounded-full bg-neutral-100 dark:bg-neutral-800 px-1 py-0.5 shadow relative">
          <Search className="h-5 w-5 text-neutral-500" />

          <Input
            type="search"
            placeholder="Search or say something..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 border-0 bg-transparent"
          />

          {queryImage && (
            <div className="relative">
              <img
                src={
                  queryImage.startsWith("data:")
                    ? queryImage
                    : convertFileSrc(queryImage)
                }
                alt="Query"
                className="h-8 w-8 rounded object-cover"
              />
              {isSearchActive && (
                <button
                  onClick={() => dispatch(clearSearch())}
                  className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-600 text-white text-[10px] flex items-center justify-center"
                  title="Close"
                >
                  ✕
                </button>
              )}
            </div>
          )}

          <FaceSearchDialog />

          {/* Voice Button */}
          <button
            onClick={startListening}
            aria-label="Start voice search"
            title="Start voice search"
            className="p-3 rounded-full bg-purple-600 hover:bg-purple-700 transition shadow-md flex items-center justify-center z-50"
          >
            <Mic className="h-6 w-6 text-white" />
          </button>

          {filtered.length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-1 bg-white dark:bg-neutral-900 shadow-lg drop-shadow-xl rounded-xl z-50 max-h-64 overflow-y-auto border border-gray-200 dark:border-neutral-700">
              {filtered.map((key, idx) => (
                <div
                  key={key}
                  className={`px-4 py-2 cursor-pointer capitalize transition-colors duration-200 ${
                    idx === activeIndex
                      ? "bg-purple-100 dark:bg-purple-700 text-purple-700 dark:text-white"
                      : "hover:bg-neutral-100 dark:hover:bg-neutral-700"
                  }`}
                  onMouseDown={() => goToPage(key)}
                >
                  {key}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* RIGHT */}
      <div className="flex items-center gap-4">
        <ThemeSelector />
        <span className="text-sm hidden sm:inline">
          Welcome <span className="text-muted-foreground">{userName}</span>
        </span>
        <a href="/settings">
          <img
            src={userAvatar || "/photo1.png"}
            alt="User Picture"
            className="h-9 w-9 rounded-full hover:ring-2 hover:ring-primary transition"
          />
        </a>
      </div>

      {/* Error Dialog */}
      {error && <ErrorDialog message={error} onClose={() => setError(null)} />}

      {/* Voice Modal */}
      {voiceOpen && (
        <div className="fixed top-40 left-[256px] right-4 z-[1000] flex justify-center">
          <div className="relative bg-white dark:bg-black/95 backdrop-blur-md rounded-3xl shadow-2xl p-6 w-full max-w-sm text-center border border-white/20 dark:border-neutral-700/50">

            <button
              onClick={() => setVoiceOpen(false)}
              className="absolute top-3 right-3 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 font-bold"
            >
              ✕
            </button>

            <div className="relative mx-auto mb-4 flex items-center justify-center">
              <div className="animate-ping absolute h-16 w-16 rounded-full bg-purple-500 opacity-30"></div>
              <div className="relative h-16 w-16 rounded-full bg-gradient-to-r from-purple-600 to-blue-500 flex items-center justify-center shadow-lg">
                <Mic className="h-7 w-7 text-white" />
              </div>
            </div>

            <p className="text-lg font-medium mt-2 text-neutral-800 dark:text-white break-words">
              {voiceText}
            </p>
            <p className="text-sm text-neutral-500 dark:text-neutral-300 mt-1">
              Speak now…
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Navbar;
