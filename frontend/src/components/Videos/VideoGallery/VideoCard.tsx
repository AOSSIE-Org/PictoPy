const VideoCard = ({ video }: { video: any }) => (
  <div
    key={video.id}
    className="relative overflow-hidden rounded-lg shadow-lg group hover:shadow-xl hover:-translate-y-2 transition-transform duration-300 ease-in-out dark:bg-card dark:text-card-foreground"
  >
    <a href="#" className="absolute inset-0 z-10">
      <span className="sr-only">View</span>
    </a>
    <video
      controls
      src={video.src}
      className="object-cover w-full h-64 transition-opacity duration-300"
    />
    
  </div>
);

export default VideoCard;
