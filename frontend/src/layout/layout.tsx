import { Navbar } from '@/components/Navigation/Navbar/Navbar';
import { AppSidebar } from '@/components/Navigation/Sidebar/AppSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { Outlet, useLocation } from 'react-router';
import { clearSearch } from '@/features/searchSlice';
import { useDispatch } from 'react-redux';
import { useEffect } from 'react';
import { ROUTES } from '@/constants/routes';
const Layout: React.FC = () => {
  const dispatch = useDispatch();
  const location = useLocation();
  useEffect(() => {
    // The face search results page owns the search state while it is open;
    // leaving it for any other page resets the search.
    if (location.pathname !== `/${ROUTES.FACE_SEARCH}`) {
      dispatch(clearSearch());
    }
  }, [location, dispatch]);

  return (
    <SidebarProvider>
      <div className="flex w-full flex-col">
        <Navbar />
        <div className="flex" style={{ height: 'calc(100vh - 56px)' }}>
          <AppSidebar />
          {/* Contain scrolling here so Navbar's parent height never exceeds 100vh — now the navbar is stuck it will not go away.
              hide-scrollbar keeps overflow-y-auto (needed for the sticky navbar) from painting a second, default scrollbar on Windows/WebView2. */}
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
