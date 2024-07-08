import { Image } from "@/types/image";

export function sortImages(
  images: Image[],
  sortBy: "date" | "title" | "popularity"
): Image[] {
  return images.slice().sort((a, b) => {
    switch (sortBy) {
      case "date":
        return new Date(b.date).getTime() - new Date(a.date).getTime();
      case "title":
        return a.title.localeCompare(b.title);
      case "popularity":
        return b.popularity - a.popularity;
      default:
        return 0;
    }
  });
}
