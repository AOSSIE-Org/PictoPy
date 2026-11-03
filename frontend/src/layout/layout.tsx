import { Navbar } from '@/components/Navigation/Navbar/Navbar';
import { AppSidebar } from '@/components/Navigation/Sidebar/AppSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { Outlet, useLocation } from 'react-router';
import { clearSearch } from '@/features/searchSlice';
import { useDispatch } from 'react-redux';
import { useEffect } from 'react';
import { isFaceSearchLocation } from '@/utils/faceSearch';
const Layout: React.FC = () => {
  const dispatch = useDispatch();
  const location = useLocation();
  useEffect(() => {
    // The face search results page owns the search state while it is open;
    // leaving it for any other page resets the search.
    if (!isFaceSearchLocation(location)) {
      dispatch(clearSearch());
    }
  }, [location, dispatch]);

  return (
    <SidebarProvider>
      <div className="flex w-full flex-col">
        <Navbar />
        <div className="flex" style={{ height: 'calc(100vh - 56px)' }}>
          <AppSidebar />
          {/* Scrolling is contained here so the Navbar's parent never exceeds
              100vh and the navbar stays put. hide-scrollbar stops WebView2 from
              painting a second scrollbar beside the one overflow-y-auto adds. */}
          <div
            id="main-scroll-container"
            className="hide-scrollbar m-4 w-full overflow-y-auto"
          >
            <Outlet />
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Layout;
