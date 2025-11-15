// // src/components/ViewModeToggle.tsx
// import React from 'react';
// import { useDispatch, useSelector } from 'react-redux';
// import { RootState } from '@/app/store';
// import { setViewMode, ViewMode } from '@/features/viewModeSlice';

// const modes: { key: ViewMode; label: string }[] = [
//   { key: 'chronological', label: 'Chronological' },
//   { key: 'grid', label: 'Grid' },
//   { key: 'list', label: 'List' },
//   { key: 'masonry', label: 'Masonry' },
// ];

// export const ViewModeToggle: React.FC = () => {
//   const dispatch = useDispatch();
//   const active = useSelector((s: RootState) => s.viewMode.mode);

//   return (
//     <div className="flex items-center gap-2 px-2 py-1">
//       {modes.map((m) => {
//         const isActive = active === m.key;

//         return (
//           <button
//             key={m.key}
//             onClick={() => dispatch(setViewMode(m.key))}
//             aria-pressed={isActive}
//             title={`Switch to ${m.label} view`}
//             className={`
//               text-sm rounded-md px-3 py-1 
//               transition-all duration-150 select-none

//               ${
//                 isActive
//                   ? // ACTIVE BLUE
//                     'bg-blue-600 text-white dark:bg-blue-800 dark:text-white'
//                   : // NORMAL STATE
//                     'bg-transparent text-gray-700 dark:text-gray-300'
//               }

//               // HOVER BLUE FOR NON-ACTIVE BUTTONS
//               ${
//                 !isActive
//                   ? 'hover:bg-blue-100 hover:text-blue-700 dark:hover:bg-blue-900/40 dark:hover:text-blue-300'
//                   : ''
//               }
//             `}
//           >
//             {m.label}
//           </button>
//         );
//       })}
//     </div>
//   );
// };

// export default ViewModeToggle;




// src/components/ViewModeToggle.tsx
import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import { setViewMode, ViewMode } from '@/features/viewModeSlice';

import {
  Calendar,
  Grid,
  List,
  LayoutGrid,
} from 'lucide-react'; // ICONS

const modes: { key: ViewMode; icon: React.ReactNode; label: string }[] = [
  { key: 'chronological', icon: <Calendar size={18} />, label: 'Chronological' },
  { key: 'grid', icon: <Grid size={18} />, label: 'Grid' },
  { key: 'list', icon: <List size={18} />, label: 'List' },
  { key: 'masonry', icon: <LayoutGrid size={18} />, label: 'Masonry' },
];

export const ViewModeToggle: React.FC = () => {
  const dispatch = useDispatch();
  const active = useSelector((s: RootState) => s.viewMode.mode);

  return (
    <div className="flex items-center gap-2 px-2 py-1">
      {modes.map((m) => {
        const isActive = active === m.key;

        return (
          <button
            key={m.key}
            onClick={() => dispatch(setViewMode(m.key))}
            aria-pressed={isActive}
            title={m.label}
            className={`
              p-2 rounded-md transition-all duration-150

              flex items-center justify-center
              text-gray-700 dark:text-gray-300

              ${
                isActive
                  ? 'bg-blue-600 text-white dark:bg-blue-800'
                  : 'hover:bg-blue-100 hover:text-blue-700 dark:hover:bg-blue-900/40 dark:hover:text-blue-300'
              }
            `}
          >
            {m.icon}
          </button>
        );
      })}
    </div>
  );
};

export default ViewModeToggle;
