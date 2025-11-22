import React, { useState, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { ThemeSelector } from "@/components/ThemeToggle";
import { Search, Mic } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";
import { selectAvatar, selectName } from "@/features/onboardingSelectors";
import { clearSearch } from "@/features/searchSlice";
import { convertFileSrc } from "@tauri-apps/api/core";
import { FaceSearchDialog } from "@/components/Dialog/FaceSearchDialog";
import { VoiceCommand } from "@/components/Dialog/VoiceCommand";
/* -------------------------------------------------------
   ERROR DIALOG
------------------------------------------------------- */
const ErrorDialog = ({ message, onClose }: { message: string; onClose: () => void }) => (
  <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
    <div className="relative w-full max-w-sm rounded-2xl border border-white/20 bg-white p-6 text-center shadow-2xl dark:border-neutral-700/50 dark:bg-neutral-900">
      <h2 className="mb-2 text-xl font-semibold text-red-600">Error</h2>
      <p className="text-sm text-neutral-700 dark:text-neutral-300">{message}</p>
      <button
        onClick={onClose}
        className="absolute top-3 right-3 font-bold text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
      >
        ✕
      </button>
    </div>
  </div>
);

/* -------------------------------------------------------
   NAVBAR
------------------------------------------------------- */
export function Navbar() {
  const userName = useSelector(selectName);
  const userAvatar = useSelector(selectAvatar);
  const searchState = useSelector((state: any) => state.search);
  const dispatch = useDispatch();

  const isSearchActive = searchState.active;
  const queryImage = searchState.queryImage;

  const recognitionRef = useRef<any>(null);

  /* ROUTES */
  const routeMap: Record<string, string> = {
    home: "/",
    albums: "/albums",
    videos: "/videos",
    settings: "/settings",
    "ai-tagging": "/ai-tagging",
    memories: "/memories",
    favourites: "/favourites",
  };

  const suggestionKeys = Object.keys(routeMap);

  /* STATES */
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [voiceText, setVoiceText] = useState("Listening...");
  const [error, setError] = useState<string | null>(null);

  const filtered =
    query.length > 0
      ? suggestionKeys.filter((s) =>
          s.toLowerCase().includes(query.toLowerCase().replace(/\s+/g, "-"))
        )
      : [];

  /* -------------------------------------------------------
     FIXED: ALWAYS CLEAR SEARCH BEFORE NAVIGATION
------------------------------------------------------- */
  const goToPage = (label: string) => {
    dispatch(clearSearch()); // ⭐ CRITICAL FIX ⭐

    const key = label.trim().toLowerCase().replace(/\s+/g, "-");

    if (routeMap[key]) {
      window.location.href = routeMap[key];
    } else {
      setError(`The page "${label}" does not exist.`);
    }
  };

  /* KEYBOARD HANDLING */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!filtered.length) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1) % filtered.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((prev) => (prev <= 0 ? filtered.length - 1 : prev - 1));
    } else if (e.key === "Enter") {
      if (activeIndex >= 0) {
        goToPage(filtered[activeIndex]);
        setActiveIndex(-1);
      }
    }
  };

  useEffect(() => {
    setActiveIndex(-1);
  }, [query]);

  /* -------------------------------------------------------
     VOICE SEARCH
------------------------------------------------------- */
  const startListening = () => {
    const SR =
      (window as any).webkitSpeechRecognition ||
      (window as any).SpeechRecognition;

    if (!SR) {
      setError("Speech recognition is not supported in your browser.");
      return;
    }

    const recog = new SR();
    recognitionRef.current = recog;

    recog.lang = "en-US";
    recog.interimResults = false;

    recog.onstart = () => {
      setVoiceOpen(true);
      setVoiceText("Listening...");
    };

    recog.onresult = (e: any) => {
      const spoken = e.results[0][0].transcript.toLowerCase();
      setVoiceText(spoken);

      // PRIORITY: favourites
      if (
        spoken.includes("favourite") ||
        spoken.includes("favorite") ||
        spoken.includes("favorites") ||
        spoken.includes("favourites")
      ) {
        goToPage("favourites");
        setTimeout(() => setVoiceOpen(false), 900);
        return;
      }

      const found = suggestionKeys.find((k) =>
        spoken.replace(/\s+/g, "-").includes(k)
      );

      if (found) {
        goToPage(found);
      } else {
        setError(`No matching page found for "${spoken}".`);
      }

      setTimeout(() => setVoiceOpen(false), 1200);
    };

    recog.onerror = () => {
      setVoiceText("Couldn't understand. Try again.");
      setTimeout(() => setVoiceOpen(false), 1200);
    };

    recog.start();
  };

  /* -------------------------------------------------------
     UI
------------------------------------------------------- */
  return (
    <div className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b bg-white/70 px-4 backdrop-blur dark:bg-black/40">
      {/* LEFT */}
      <div className="flex w-[256px] items-center gap-2">
        <img src="/128x128.png" width={32} height={32} alt="PictoPy Logo" />
        <span className="text-xl font-bold">PictoPy</span>
      </div>

      {/* CENTER */}
      <div className="relative mx-auto flex max-w-xl flex-1 justify-center px-4">
        <div className="relative flex w-full items-center gap-2 rounded-full bg-neutral-100 px-2 py-1 shadow dark:bg-neutral-800">
          <Search className="h-5 w-5 text-neutral-500" />

          <Input
            type="search"
            placeholder="Search or say something..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 border-0 bg-transparent"
          />

          {/* Query Image Preview */}
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
                  className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-600 text-[10px] text-white"
                >
                  ✕
                </button>
              )}
            </div>
          )}

          <FaceSearchDialog />

          {/* MIC */}
          <button
            onClick={startListening}
            aria-label="Start voice search"
            className="z-50 flex items-center justify-center rounded-full bg-purple-600 p-3 shadow-md hover:bg-purple-700"
          >
            <Mic className="h-6 w-6 text-white" />
          </button>

          {/* DROPDOWN */}
          {filtered.length > 0 && (
            <div className="absolute top-full right-0 left-0 z-50 mt-1 max-h-64 overflow-y-auto rounded-xl border bg-white shadow-lg dark:border-neutral-700 dark:bg-neutral-900">
              {filtered.map((key, idx) => (
                <div
                  key={key}
                  className={`cursor-pointer px-4 py-2 capitalize ${
                    idx === activeIndex
                      ? "bg-purple-100 text-purple-700 dark:bg-purple-700 dark:text-white"
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
        <span className="hidden text-sm sm:inline">
          Welcome <span className="text-muted-foreground">{userName}</span>
        </span>
        <a href="/settings">
          <img
            src={userAvatar || "/photo1.png"}
            alt="User"
            className="h-9 w-9 rounded-full hover:ring-2 hover:ring-purple-500 transition"
          />
        </a>
      </div>

      {/* ERROR */}
      {error && <ErrorDialog message={error} onClose={() => setError(null)} />}

      {/* VOICE MODAL */}
      {voiceOpen && (
        <div className="fixed top-40 right-4 left-[256px] z-[2000] flex justify-center">
          <div className="relative w-full max-w-sm rounded-3xl border bg-white p-6 text-center shadow-xl dark:bg-black dark:border-neutral-700/50">
            <Mic className="h-7 w-7 mx-auto text-purple-600" />
            <p className="mt-3 text-lg font-medium">{voiceText}</p>
            <p className="text-sm text-neutral-500">Listening...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Navbar;
