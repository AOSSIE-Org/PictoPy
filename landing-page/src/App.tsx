import { useContext, useEffect } from "react";
import { ThemeProvider, ThemeContext, ThemeOptions } from "./context/theme-provider";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./Pages/Landing page/Navbar";
import InteractiveDemo from "./Pages/Demo/marqu";
import FAQ from "./Pages/FaqPage/FAQ"; // Ensure this is a default import

// Import the Home component
import Home from "./Pages/Landing page/Home1"; // Correct the path if necessary
import HowItWorks from "./Pages/HowItWorks/HowItWorks";
import Footer from "./Pages/Footer/Footer";
import PictopyLanding from "./Pages/pictopy-landing";
import BouncyCardsFeatures from "./components/ui/Bouncy Card Features";
import { ScrollProgress } from "./components/ui/ScrollProgress";

function HomePage() {
  return (
    <>
      <Home /> {/* This will now render the Home component */}
      <ScrollProgress></ScrollProgress>
      <InteractiveDemo />
      <HowItWorks />
      <BouncyCardsFeatures />
      <PictopyLanding />
      <FAQ />
      <Footer />
    </>
  );
}

function AppContent() {

  return (
    <Router>
      <Navbar />
      <div className="relative pt-20">
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </div>
    </Router>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
