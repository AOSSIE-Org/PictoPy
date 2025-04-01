import React from 'react';
import { createPortal } from 'react-dom';
import Notification from './Notification';

interface NotificationPortalProps {
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
  }>;
  onClose: (id: string) => void;
}

const NotificationPortal: React.FC<NotificationPortalProps> = ({
  notifications,
  onClose,
}) => {
  return createPortal(
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2">
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          type={notification.type}
          message={notification.message}
          onClose={() => onClose(notification.id)}
        />
      ))}
    </div>,
    document.body,
  );
};

export default NotificationPortal;
