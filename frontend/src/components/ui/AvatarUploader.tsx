import React, { useState, useEffect } from 'react';

const AvatarUploader: React.FC = () => {
  const [avatar, setAvatar] = useState<string | null>(null);

  useEffect(() => {
    const savedAvatar = localStorage.getItem('userAvatar');
    if (savedAvatar) {
      setAvatar(savedAvatar);
    }
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        const base64Image = reader.result as string;
        localStorage.setItem('userAvatar', base64Image); // Save in local storage
        setAvatar(base64Image);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="flex flex-col items-center space-y-4 p-4">
      {avatar ? (
        <img
          src={avatar}
          alt="User Avatar"
          className="rounded-full h-20 w-20 border-2 border-gray-300"
        />
      ) : (
        <div className="rounded-full flex h-20 w-20 items-center justify-center bg-gray-200 text-gray-500">
          No Avatar
        </div>
      )}
      <label className="cursor-pointer rounded-lg bg-blue-500 px-4 py-2 text-white hover:bg-blue-600">
        Choose File
        <input type="file" className="hidden" onChange={handleFileChange} />
      </label>
    </div>
  );
};

export default AvatarUploader;
