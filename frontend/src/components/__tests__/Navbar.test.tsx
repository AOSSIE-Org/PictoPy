import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Navbar } from '../Navigation/Navbar/Navbar';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { setClusters } from '@/features/faceClustersSlice';
import { selectName, selectAvatar } from '@/features/onboardingSelectors';

// Mock dependencies
jest.mock('react-redux', () => ({
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

interface LinkProps {
  children: React.ReactNode;
  to: string;
}

jest.mock('react-router', () => ({
  useNavigate: jest.fn(),
  Link: ({ children, to }: LinkProps) => (
    <a href={to} data-testid="link">
      {children}
    </a>
  ),
}));

jest.mock('@/hooks/useQueryExtension', () => ({
  usePictoQuery: jest.fn(),
}));

jest.mock('@/api/api-functions', () => ({
  fetchAllClusters: jest.fn(),
}));

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: jest.fn((src) => src),
}));

jest.mock('@/components/Dialog/FaceSearchDialog', () => ({
  FaceSearchDialog: () => <div data-testid="face-search-dialog" />,
}));

jest.mock('@/components/ThemeToggle', () => ({
  ThemeSelector: () => <div data-testid="theme-selector" />,
}));

// Mock framer-motion to render immediately without animations
jest.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: any) => <>{children}</>,
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

interface TestCluster {
  cluster_id: string;
  cluster_name: string;
  face_count: number;
  face_image_base64?: string;
}

describe('Navbar Component', () => {
  let mockDispatch: jest.Mock;
  let mockNavigate: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockDispatch = jest.fn();
    mockNavigate = jest.fn();

    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    (useNavigate as unknown as jest.Mock).mockReturnValue(mockNavigate);

    (usePictoQuery as jest.Mock).mockReturnValue({
      data: null,
      isSuccess: false,
    });
  });

  const setupUseSelector = (clusters: TestCluster[] = []) => {
    (useSelector as unknown as jest.Mock).mockImplementation((selector) => {
      if (selector === selectName) return 'Test User';
      if (selector === selectAvatar) return '/test-avatar.png';

      const mockState = {
        search: { active: false, queryImage: null },
        faceClusters: { clusters },
      };
      return selector(mockState);
    });
  };

  it('toggles expansion (open/close) when clicking the search input', () => {
    setupUseSelector([]);
    render(<Navbar />);

    // Initially closed
    expect(screen.queryByText('Favourites')).not.toBeInTheDocument();

    // Click to open
    const searchInput = screen.getByPlaceholderText('Add to your search');
    fireEvent.click(searchInput);

    expect(screen.getByText('Favourites')).toBeInTheDocument();
  });

  it('closes dropdown when clicking outside', () => {
    setupUseSelector([]);
    render(<Navbar />);

    // Open dropdown
    fireEvent.click(screen.getByPlaceholderText('Add to your search'));
    expect(screen.getByText('Favourites')).toBeInTheDocument();

    // Click outside
    fireEvent.mouseDown(document.body);

    expect(screen.queryByText('Favourites')).not.toBeInTheDocument();
  });

  it('closes dropdown when Escape key is pressed', () => {
    setupUseSelector([]);
    render(<Navbar />);

    // Open dropdown
    fireEvent.click(screen.getByPlaceholderText('Add to your search'));
    expect(screen.getByText('Favourites')).toBeInTheDocument();

    // Press Escape
    fireEvent.keyDown(document, { key: 'Escape' });

    expect(screen.queryByText('Favourites')).not.toBeInTheDocument();
  });

  it('triggers usePictoQuery fetch only when enabled (isExpanded and clusters empty)', () => {
    setupUseSelector([]);

    const { rerender } = render(<Navbar />);

    // Initially not expanded, should be disabled
    expect(usePictoQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        enabled: false,
      }),
    );

    // Open dropdown, no clusters yet -> enabled should be true
    fireEvent.click(screen.getByPlaceholderText('Add to your search'));

    expect(usePictoQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        enabled: true,
      }),
    );

    // Mock that we now have clusters
    setupUseSelector([
      { cluster_id: '1', cluster_name: 'Person A', face_count: 0 },
    ]);
    rerender(<Navbar />);

    // Now it should be disabled because clusters exist
    expect(usePictoQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        enabled: false,
      }),
    );
  });

  it('closes dropdown on navigation (route change)', () => {
    setupUseSelector([]);
    render(<Navbar />);

    // Open dropdown
    fireEvent.click(screen.getByPlaceholderText('Add to your search'));
    expect(screen.getByText('Favourites')).toBeInTheDocument();

    // Click Favourites
    fireEvent.click(screen.getByText('Favourites'));

    // Should navigate to /favourites
    expect(mockNavigate).toHaveBeenCalledWith('/favourites');

    // Dropdown should be closed
    expect(screen.queryByText('Favourites')).not.toBeInTheDocument();
  });

  it('dispatches setClusters when clustersData and clustersSuccess are present', () => {
    setupUseSelector([]);

    const mockClusters: TestCluster[] = [
      { cluster_id: '1', cluster_name: 'Test Cluster', face_count: 0 },
    ];

    // Mock usePictoQuery to return success with data
    (usePictoQuery as jest.Mock).mockReturnValue({
      data: {
        data: {
          clusters: mockClusters,
        },
      },
      isSuccess: true,
    });

    render(<Navbar />);

    expect(mockDispatch).toHaveBeenCalledWith(setClusters(mockClusters));
  });

  it('toggles expansion (open/close) when focusing the search input', () => {
    setupUseSelector([]);
    render(<Navbar />);

    expect(screen.queryByText('Favourites')).not.toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText('Add to your search');
    // Focus the input directly using fireEvent
    fireEvent.focus(searchInput);
    expect(screen.getByText('Favourites')).toBeInTheDocument();
  });

  it('renders a maximum of 6 face clusters even if the store has more', () => {
    const manyClusters: TestCluster[] = Array.from({ length: 10 }, (_, i) => ({
      cluster_id: `id-${i}`,
      cluster_name: `Person ${i}`,
      face_count: 0,
    }));
    setupUseSelector(manyClusters);
    render(<Navbar />);

    fireEvent.click(screen.getByPlaceholderText('Add to your search'));

    // "Person 0" through "Person 5" should be present
    expect(screen.getByText('Person 0')).toBeInTheDocument();
    expect(screen.getByText('Person 5')).toBeInTheDocument();

    // "Person 6" through "Person 9" should NOT be present
    expect(screen.queryByText('Person 6')).not.toBeInTheDocument();
    expect(screen.queryByText('Person 9')).not.toBeInTheDocument();
  });

  it('does not render FaceClustersRow when clusters array is empty', () => {
    setupUseSelector([]);
    render(<Navbar />);
    fireEvent.click(screen.getByPlaceholderText('Add to your search'));

    expect(screen.getByText('Favourites')).toBeInTheDocument();
    expect(screen.getByText('See all people')).toBeInTheDocument();

    // Avatar fallbacks or names shouldn't be rendered
    // queryByText(/Person/) would match cluster fallback names if any were rendered
    expect(screen.queryByText(/Person/)).not.toBeInTheDocument();
  });

  it('renders correct fallback initials and labels when face_image_base64 and cluster_name are absent', () => {
    const fallbackClusters: TestCluster[] = [
      {
        cluster_id: '1234abcd',
        cluster_name: 'John Doe',
        face_count: 0,
      },
      { cluster_id: '5678efgh', cluster_name: '', face_count: 0 },
    ];
    setupUseSelector(fallbackClusters);
    render(<Navbar />);
    fireEvent.click(screen.getByPlaceholderText('Add to your search'));

    // First cluster: should have J in fallback, and "John Doe" as text
    expect(screen.getByText('J')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();

    // Second cluster: should have 5 in fallback, and "Person efgh" as text
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Person efgh')).toBeInTheDocument();
  });

  it('navigates to specific cluster and closes dropdown when clicking an avatar chip', () => {
    setupUseSelector([
      { cluster_id: 'cluster-123', cluster_name: 'Test Person', face_count: 0 },
    ]);
    render(<Navbar />);
    fireEvent.click(screen.getByPlaceholderText('Add to your search'));

    fireEvent.click(screen.getByText('Test Person'));

    expect(mockNavigate).toHaveBeenCalledWith('/person/cluster-123');
    expect(screen.queryByText('Favourites')).not.toBeInTheDocument();
  });

  it('navigates to AI tagging page when clicking "See all people"', () => {
    setupUseSelector([]);
    render(<Navbar />);
    fireEvent.click(screen.getByPlaceholderText('Add to your search'));

    fireEvent.click(screen.getByText('See all people'));

    expect(mockNavigate).toHaveBeenCalledWith('/ai-tagging');
    expect(screen.queryByText('See all people')).not.toBeInTheDocument();
  });
});
