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
  <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/50 p-4 backdrop-blur-md">
    <div className="relative w-full max-w-sm rounded-2xl border bg-white dark:bg-neutral-900 p-6 shadow-xl">
      <button onClick={onClose} className="absolute top-2 right-3 text-xl font-bold">✕</button>
      <h2 className="mb-2 text-xl font-semibold text-red-600">Error</h2>
      <p className="text-sm text-neutral-700 dark:text-neutral-300">{message}</p>
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

  const goToPage = (label: string) => {
    dispatch(clearSearch());
    const key = label.trim().toLowerCase().replace(/\s+/g, "-");

    if (routeMap[key]) {
      window.location.href = routeMap[key];
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
    } else if (e.key === "Enter" && activeIndex >= 0) {
      goToPage(filtered[activeIndex]);
      setActiveIndex(-1);
    }
  };

  useEffect(() => setActiveIndex(-1), [query]);

  const startListening = () => {
    setVoiceOpen(true);
    setQuery("");       // HIDE suggestions
    setActiveIndex(-1); // RESET dropdown selection

    const SR =
      (window as any).webkitSpeechRecognition ||
      (window as any).SpeechRecognition;

    if (!SR) {
      setError("Speech recognition is not supported in your browser.");
      setVoiceOpen(false);
      return;
    }

    const recog = new SR();
    recognitionRef.current = recog;
    recog.lang = "en-US";
    recog.interimResults = false;

    recog.onresult = (e: any) => {
      const spoken = e.results[0][0].transcript.toLowerCase();
      setVoiceText(spoken);

      if (
        spoken.includes("favorite") ||
        spoken.includes("favourite") ||
        spoken.includes("favorites") ||
        spoken.includes("favourites")
      ) {
        goToPage("favourites");
        setTimeout(() => setVoiceOpen(false), 800);
        return;
      }

      const found = suggestionKeys.find((k) =>
        spoken.replace(/\s+/g, "-").includes(k)
      );

      found ? goToPage(found) : setError(`No matching page found for "${spoken}".`);
      setTimeout(() => setVoiceOpen(false), 1000);
    };

    recog.onerror = () => {
      setVoiceText("Try again");
      setTimeout(() => setVoiceOpen(false), 800);
    };

    recog.start();
  };

  return (
    <div className="sticky top-0 z-50 flex h-14 w-full items-center justify-between border-b bg-white/60 px-4 backdrop-blur-md dark:bg-black/60">
      <a href="/" className="flex items-center gap-2">
        <img src="/128x128.png" width={32} height={32} />
        <span className="text-xl font-bold">PictoPy</span>
      </a>

      <div className="relative mx-auto w-full max-w-lg flex-1">
        <div className="flex items-center gap-2 rounded-full bg-neutral-100 px-3 py-1 shadow dark:bg-neutral-800">
          <Search className="h-5 w-5 text-neutral-500" />

          <Input
            placeholder="Search or speak…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 border-0 bg-transparent focus-visible:ring-0"
          />

          <FaceSearchDialog />

          <button
            onClick={startListening}
            className="rounded-full bg-purple-600 p-2 hover:bg-purple-700"
          >
            <Mic className="h-5 w-5 text-white" />
          </button>
        </div>

        {/* Suggestions appear ONLY if voice dialog is closed */}
        {!voiceOpen && filtered.length > 0 && (
          <div className="absolute top-full w-full z-50 mt-1 rounded-xl border bg-white shadow-xl dark:bg-neutral-900">
            {filtered.map((key, idx) => (
              <div
                key={key}
                onMouseDown={() => goToPage(key)}
                className={`px-4 py-2 cursor-pointer capitalize ${
                  idx === activeIndex
                    ? "bg-purple-200 dark:bg-purple-700"
                    : "hover:bg-neutral-200 dark:hover:bg-neutral-700"
                }`}
              >
                {key}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <ThemeSelector />
        <span className="hidden sm:inline text-sm">
          Welcome <span className="text-muted-foreground">{userName}</span>
        </span>
        <a href="/settings">
          <img
            src={userAvatar || "/photo1.png"}
            className="h-8 w-8 rounded-full hover:ring-2 hover:ring-purple-500"
          />
        </a>
      </div>

      {error && <ErrorDialog message={error} onClose={() => setError(null)} />}

      {voiceOpen && (
        <div className="fixed top-28 left-0 right-0 flex justify-center z-[2000]">
          <div className="relative max-w-sm w-full rounded-3xl p-6 bg-white border shadow-xl dark:bg-neutral-900">
            <button className="absolute top-3 right-4 text-xl font-bold" onClick={() => setVoiceOpen(false)}>
              ✕
            </button>
            <Mic className="h-7 w-7 mx-auto text-purple-600" />
            <p className="mt-3 text-lg font-medium text-center">{voiceText}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Navbar;
