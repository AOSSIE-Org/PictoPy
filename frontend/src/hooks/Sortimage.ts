import { useEffect, useState } from 'react';

interface Image {
    id: string;
    date: string;
    title: string;
    popularity: number;
    src: string;
    tags: string[];
}

function useSortedImages(data: any): Image[] {
    const [sortedImages, setSortedImages] = useState<Image[]>([]);

    useEffect(() => {
        const parseAndSortImageData = (data: any): Image[] => {
            const images: Image[] = [];

            for (const filePath in data) {
                if (Object.prototype.hasOwnProperty.call(data, filePath)) {
                    const tags = data[filePath].split(', ');
                    const fileName = filePath.substring(filePath.lastIndexOf('/') + 1);

                    const image: Image = {
                        id: fileName,
                        date: "",
                        title: data[filePath],
                        popularity: tags.length,
                        src: filePath,
                        tags: tags
                    };

                    images.push(image);
                }
            }

            images.sort((a, b) => b.popularity - a.popularity);

            return images;
        };

        const sortedImages = parseAndSortImageData(data);

        setSortedImages(sortedImages);
    }, []);

    return sortedImages;
}

export default useSortedImages;
