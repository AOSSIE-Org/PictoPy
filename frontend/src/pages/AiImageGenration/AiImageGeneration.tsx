import React, { useState } from 'react';
import { Download, Link, Sparkles, Heart, Eraser, Wand2 } from 'lucide-react';

const AiImageGeneration = () => {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [error, setError] = useState(null);
  const [showCopied, setShowCopied] = useState(false);

  const [magicWords] = useState(['mystical', 'ethereal', 'vibrant', 'dreamy', 'cosmic']);
  const [selectedStyle, setSelectedStyle] = useState('');
  const [showTooltip, setShowTooltip] = useState('');
  const [imageScale, setImageScale] = useState(1);

  const artStyles = [
    { name: '🎨 Artistic', key: 'artistic' },
    { name: '📷 Realistic', key: 'realistic' },
    { name: '✨ Fantasy', key: 'fantasy' },
    { name: '🌌 Cosmic', key: 'cosmic' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt) return;

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/images/generate-image?prompt=${encodeURIComponent(prompt)}`, {
        method: 'POST',
      });

      console.log(response)
      if (!response.ok) {
        throw new Error('Failed to generate image.');
      }

      const data = await response.json();
      if (data.image) {
        setGeneratedImage(`data:image/png;base64,${data.image}`);
      } else {
        setError('Image generation failed. No image data received.');
      }
    } catch (err) {
      setError('Failed to generate image. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleMagicWord = (word) => {
    setPrompt((prev) => `${prev} ${word}`.trim());
  };

  const handleStyleSelect = (style) => {
    setSelectedStyle(style);
    setPrompt((prev) => `${prev} in ${style} style`.trim());
  };

  return (
    <div className="min-h-screen w-full bg-white dark:bg-gray-900 transition-colors flex flex-col">
      <div className="flex-1 w-full container mx-auto px-6 py-16 max-w-4xl">
        {/* Interactive Header */}
        <div className="text-center mb-16 animate-fade-in relative">
          <h1
            className="text-6xl font-extrabold mb-4 relative inline-block text-gray-900 dark:text-white cursor-pointer transform transition-transform hover:scale-105"
            onMouseEnter={() => setShowTooltip('Create something magical!')}
            onMouseLeave={() => setShowTooltip('')}
          >
            PictoPy
            <Sparkles className="absolute -top-6 -right-8 h-8 w-8 text-purple-500 animate-bounce" />
          </h1>
          {showTooltip && (
            <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-purple-500 text-white px-4 py-2 rounded-lg text-sm animate-fade-in">
              {showTooltip}
            </div>
          )}
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Where imagination meets artificial intelligence - Create stunning visuals with our
            advanced AI image generator.
          </p>
        </div>

        {/* Magic Words Bar */}
        <div className="mb-6 flex flex-wrap gap-2 justify-center">
          {magicWords.map((word) => (
            <button
              key={word}
              onClick={() => handleMagicWord(word)}
              className="px-4 py-2 bg-purple-50 dark:bg-gray-800 rounded-full text-sm font-medium text-purple-600 dark:text-purple-400 hover:bg-purple-100 dark:hover:bg-gray-700 transition-all transform hover:scale-105 hover:shadow-md"
            >
              +{word}
            </button>
          ))}
        </div>

        {/* Style Selection */}
        <div className="mb-6 flex flex-wrap gap-3 justify-center">
          {artStyles.map((style) => (
            <button
              key={style.key}
              onClick={() => handleStyleSelect(style.key)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all transform hover:scale-105 ${
                selectedStyle === style.key
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
              }`}
            >
              {style.name}
            </button>
          ))}
        </div>

        {/* Input Form */}
        <div className="w-full bg-white rounded-2xl shadow-xl p-6 hover:shadow-2xl transition-all transform hover:scale-[1.01] border border-purple-100 dark:bg-gray-800 dark:border-gray-700">
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <div className="flex-1 relative group">
              <Link className="absolute left-4 top-3.5 h-5 w-5 text-gray-400 group-hover:text-purple-500 transition-colors" />
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your imagination..."
                className="w-full pl-12 pr-24 py-3 text-gray-700 bg-white border border-gray-200 rounded-lg focus:outline-none focus:border-purple-500 transition-all hover:border-purple-300 dark:bg-gray-700 dark:text-white dark:border-gray-600 dark:focus:border-purple-400"
              />
              {prompt && (
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(prompt);
                    setShowCopied(true);
                    setTimeout(() => setShowCopied(false), 2000);
                  }}
                  className="absolute right-2 top-2 px-3 py-1 text-xs bg-gray-100 rounded-full hover:bg-purple-100 text-gray-600 hover:text-purple-600 transition-colors dark:bg-gray-600 dark:hover:bg-purple-700 dark:text-white"
                >
                  {showCopied ? '✨ Copied!' : 'Copy'}
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={isGenerating || !prompt}
              className={`px-6 py-3 rounded-lg font-medium transition-all transform hover:scale-105 ${
                isGenerating || !prompt
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-rose-500 text-white hover:shadow-lg dark:bg-purple-500 dark:hover:bg-purple-600'
              }`}
            >
              {isGenerating ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creating Magic...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Wand2 className="h-4 w-4" />
                  Generate
                </span>
              )}
            </button>
          </form>
        </div>

        {/* Generated Image Display */}
        {generatedImage && (
          <div className="mt-8 bg-white rounded-2xl shadow-xl p-6 animate-fade-in border border-purple-100 dark:bg-gray-800 dark:border-gray-700">
            <div className="relative group">
              <img
                src={generatedImage}
                alt="AI generated"
                style={{ transform: `scale(${imageScale})` }}
                className="w-full h-auto rounded-lg transition-all duration-300 hover:shadow-2xl"
                onMouseEnter={() => setImageScale(1.02)}
                onMouseLeave={() => setImageScale(1)}
              />
              <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => {
                    const link = document.createElement('a');
                    link.href = generatedImage;
                    link.download = 'pictopy-generated-image.png';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                  }}
                  className="p-3 bg-white rounded-lg shadow-lg hover:bg-purple-500 hover:text-white transform hover:scale-110 transition-all dark:bg-gray-700 dark:hover:bg-purple-500"
                >
                  <Download className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setGeneratedImage(null)}
                  className="p-3 bg-white rounded-lg shadow-lg hover:bg-rose-500 hover:text-white transform hover:scale-110 transition-all dark:bg-gray-700 dark:hover:bg-rose-500"
                >
                  <Eraser className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-lg animate-shake border border-red-100 dark:bg-red-900 dark:text-red-300 dark:border-red-700">
            {error}
          </div>
        )}
      </div>
      <footer className="text-center text-sm py-8 text-gray-500 dark:text-gray-400">
        <span className="flex items-center justify-center gap-1">
          Made with <Heart className="h-4 w-4 text-red-500 animate-pulse" /> by
          
            PictoPy Team
          
        </span>
      </footer>
    </div>
  );
};

export default AiImageGeneration;
