// components/MediaGallery/MediaCard.tsx

import { MediaCardProps } from "@/types/Media";

export default function MediaCard({ item, type }: MediaCardProps) {
  return (
    <div className="relative overflow-hidden rounded-lg shadow-lg group hover:shadow-xl hover:-translate-y-2 transition-transform duration-300 ease-in-out dark:bg-card dark:text-card-foreground">
      <a href="#" className="absolute inset-0 z-10">
        <span className="sr-only">View</span>
      </a>
      {type === "image" ? (
        <img
          src={item.src}
          alt={item.title}
          width={700}
          height={400}
          className="object-cover w-full h-64 transition-opacity duration-300"
          style={{ opacity: 1 }}
        />
      ) : (
        <video
          controls
          src={item.src}
          className="object-cover w-full h-64 transition-opacity duration-300"
        />
      )}
    </div>
  );
}
