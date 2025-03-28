import { useState, useEffect } from 'react';
import { imagesEndpoints } from '../api/apiEndpoints';
import { ThemeProvider } from './contexts/ThemeContext';
import QueryClientProviders from './Config/QueryClientProvider';
import { Outlet } from 'react-router-dom';
import LayoutApp from './layout/main';
import "./App.css";



const fetchFilePath = async () => {
  try {
    // Fetch file path from backend
    const response = await fetch(imagesEndpoints.getThumbnailPath);
    const data = await response.json();
    if (localStorage.getItem('thumbnailPath')) {
      localStorage.removeItem('thumbnailPath');
    }
    if (data.thumbnailPath) {
      // Store in localStorage
      console.log('Thumbnail Path = ', data.thumbnailPath);
      localStorage.setItem('thumbnailPath', data.thumbnailPath);
      return data.thumbnailPath;
    }
  } catch (error) {
    console.error('Error fetching file path:', error);
  }
  return null;
};

export const Layout = () => {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const init = async () => {
      const storedPath = localStorage.getItem('thumbnailPath');
      console.log('Thumbnail Path = ', storedPath);
      if (!storedPath) {
        await fetchFilePath();
      }
      setIsReady(true);
    };

    init();
  }, []);

  if (!isReady) return <p>Loading...</p>;

  return (
    <>
    <ThemeProvider>
      <QueryClientProviders>
        <LayoutApp>
          <Outlet/>
        </LayoutApp>
      </QueryClientProviders>
    </ThemeProvider>
    </>
  )
};
