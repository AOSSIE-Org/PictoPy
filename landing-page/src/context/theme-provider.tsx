import React, { useEffect, useState } from "react";

// Export the ThemeOptions enum
export enum ThemeOptions {
    Light = 0,
    Dark = 1,
}

interface ThemeContextStructure {
    theme: ThemeOptions;
    toggleTheme: () => void;
}

const defaultThemeContext: ThemeContextStructure = {
    theme: ThemeOptions.Light,
    toggleTheme: () => {},
};

export const ThemeContext = React.createContext<ThemeContextStructure>(defaultThemeContext);

// Helper function to validate theme code
function validateThemeCode(themeCode: number): boolean {
    return themeCode === ThemeOptions.Light || themeCode === ThemeOptions.Dark;
}

function getInitialTheme(): ThemeOptions {
    const storedTheme = '';
    
    if (storedTheme) {
        const themeCode = parseInt(storedTheme, 10);
        if (validateThemeCode(themeCode)) {
            return themeCode;
        }
    }

    // If no valid theme is found, use system preference
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? ThemeOptions.Dark
        : ThemeOptions.Light;

    return systemTheme;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [theme, setTheme] = useState<ThemeOptions>(getInitialTheme());

    const toggleTheme = () => {
        setTheme(prevTheme => prevTheme === ThemeOptions.Dark ? ThemeOptions.Light : ThemeOptions.Dark);
    };

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}
