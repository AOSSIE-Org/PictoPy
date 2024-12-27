import { albumEndpoints } from '../apiEndpoints';

export const createAlbums = async (payload: {
  name: string;
  description?: string;
}) => {
  const response = await fetch(albumEndpoints.createAlbum, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  return data;
};

export const deleteAlbums = async (payload: { name: string }) => {
  const response = await fetch(albumEndpoints.deleteAlbum, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  return data;
};

export const fetchAllAlbums = async () => {
  const response = await fetch(albumEndpoints.viewAllAlbums, {
    headers: {
      Accept: 'application/json',
    },
  });

  const data = await response.json();
  return data;
};

export const addToAlbum = async (payload: {
  album_name: string;
  image_path: string;
}) => {
  const response = await fetch(albumEndpoints.addToAlbum, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  return data;
};

export const addMultipleToAlbum = async (payload: {
  album_name: string;
  paths: string[];
}) => {
  const response = await fetch(albumEndpoints.addMultipleToAlbum, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  return data;
};

export const removeFromAlbum = async (payload: {
  album_name: string;
  path: string;
}) => {
  const response = await fetch(albumEndpoints.removeFromAlbum, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  return data;
};

export const viewYourAlbum = async (albumName: string) => {
  const response = await fetch(
    `${albumEndpoints.viewAlbum}?album_name=${encodeURIComponent(albumName)}`,
    {
      headers: {
        Accept: 'application/json',
      },
    },
  );

  const data = await response.json();
  return data;
};

export const editAlbumDescription = async (payload: {
  album_name: string;
  description: string;
}) => {
  const response = await fetch(albumEndpoints.editAlbumDescription, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  return data;
};

export const addMultipleToAlbums = async (payload: { paths: string[] }) => {
  const response = await fetch(albumEndpoints.addMultipleToAlbums, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  return data;
};
