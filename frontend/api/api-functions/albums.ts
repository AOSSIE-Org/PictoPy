import { albumEndpoints } from '../apiEndpoints';

interface ViewAlbumParams {
  album_name: string;
  password?: string;
}

export const createAlbums = async (payload: {
  name: string;
  description?: string;
  is_hidden?: boolean;
  password?: string;
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

export const viewYourAlbum = async ({
  album_name,
  password,
}: ViewAlbumParams) => {
  const queryParams = new URLSearchParams({ album_name });
  if (password) {
    queryParams.append('password', password);
  }

  const response = await fetch(
    `${albumEndpoints.viewAlbum}?${queryParams.toString()}`,
    {
      headers: {
        Accept: 'application/json',
      },
    },
  );

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

export const fetchAllAlbums = async (includeHidden: boolean = false) => {
  const queryParams = new URLSearchParams();
  if (includeHidden) {
    queryParams.append('include_hidden', 'true');
  }

  const url = `${albumEndpoints.viewAllAlbums}${
    includeHidden ? '?' + queryParams.toString() : ''
  }`;

  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
  });

  const data = await response.json();
  return data;
};

export const isAlbumHidden = (albumData: any): boolean => {
  return albumData?.is_hidden || false;
};

export const addToAlbum = async (payload: {
  album_name: string;
  image_path: string;
  password?: string;
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
  password?: string;
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
  password?: string;
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

export const editAlbumDescription = async (payload: {
  album_name: string;
  description: string;
  password?: string;
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
