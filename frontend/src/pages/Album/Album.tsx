import AlbumsView from '@/components/Album/Album';
import { useLoaderData } from 'react-router-dom';

function Album() {

  const data:any = useLoaderData();
  console.log("Album data = ",data);

  return (
    <>
      <AlbumsView />
    </>
  );
}

export default Album;
