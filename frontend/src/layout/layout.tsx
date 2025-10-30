import { Navbar } from '@/components/Navigation/Navbar/Navbar';
import { AppSidebar } from '@/components/Navigation/Sidebar/AppSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { Outlet, useLocation } from 'react-router';
import { clearSearch } from '@/features/searchSlice';
import { useDispatch } from 'react-redux';
import { useEffect } from 'react';
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
        <div className="flex" style={{ height: 'calc(100vh - 56px)' }}>
          <AppSidebar />
          <div className="m-4 w-full overflow-y-auto">
            <Outlet />
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Layout;
