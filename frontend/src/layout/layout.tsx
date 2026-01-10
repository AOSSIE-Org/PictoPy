import { Navbar } from '@/components/Navigation/Navbar/Navbar';
import { AppSidebar } from '@/components/Navigation/Sidebar/AppSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { Outlet, useLocation } from 'react-router';
import { clearSearch } from '@/features/searchSlice';
import { useDispatch } from 'react-redux';
import { useEffect } from 'react';
import BackToTop from '@/components/Navigation/BackToTop/BackToTop';

const Layout: React.FC = () => {
  const dispatch = useDispatch();
  const location = useLocation();
  
  useEffect(() => {
    if (location.pathname !== '/home') {
      dispatch(clearSearch());
    }
  }, [location, dispatch]);

  return (
    <SidebarProvider>
      <div className="flex w-full flex-col">
        <Navbar />
        {/* Keep your original height style, but make content scrollable */}
        <div className="flex" style={{ height: 'calc(100vh - 56px)' }}>
          <AppSidebar />
          {/* FIXED: Proper scrollable content with correct height */}
          <div 
            className="m-4 w-full overflow-y-auto" 
            style={{ 
              maxHeight: 'calc(100vh - 56px - 32px)', // Navbar + margin
              overflowY: 'auto'
            }}
          >
            <Outlet />
          </div>
        </div>
        <BackToTop />
      </div>
    </SidebarProvider>
  );
};

export default Layout;
