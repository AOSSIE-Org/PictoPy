import { albumEndpoints } from '../../api/apiEndpoints';

export const fetchAlbums = async() => {
    try {
        const url = `${albumEndpoints.viewAllAlbums}`
        const response = await fetch(url, {
            headers: {
                Accept: 'application/json',
            },
        });
        const data = await response.json();
        console.log("Album data is fetched = ",data);
        return data['data'];
    }  catch(error) {
        return []
    }
}