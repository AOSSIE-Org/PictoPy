import React, { useState } from "react";
import { Mic } from "lucide-react";

interface Props {
  onCommand: (cmd: string) => void;
}

export function VoiceCommand({ onCommand }: Props) {
  const [listening, setListening] = useState(false);

  const startListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.start();
    setListening(true);

    recognition.onresult = (event: any) => {
      const spokenText = event.results[0][0].transcript.toLowerCase().trim();
      setListening(false);

      console.log("Recognized:", spokenText);
      onCommand(spokenText); // send recognized speech to navbar
    };

    recognition.onerror = () => {
      setListening(false);
      alert("Try again...");
    };
  };

  return (
    <button
      onClick={startListening}
      aria-label="Start voice search"
      className="z-50 flex items-center justify-center rounded-full bg-purple-600 p-3 shadow-md hover:bg-purple-700 transition"
    >
      {listening ? (
        <span className="text-white text-[10px] font-semibold">Listening...</span>
      ) : (
        <Mic className="h-5 w-5 text-white" />
      )}
    </button>
  );
}
