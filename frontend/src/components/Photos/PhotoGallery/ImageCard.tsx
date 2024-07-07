const ImageCard = ({ image }: { image: any }) => (
  <div
    key={image.id}
    className="relative overflow-hidden rounded-lg shadow-lg group hover:shadow-xl hover:-translate-y-2 transition-transform duration-300 ease-in-out dark:bg-card dark:text-card-foreground"
  >
    <a href="#" className="absolute inset-0 z-10">
      <span className="sr-only">View</span>
    </a>
    <img
      src={image.src}
      alt={image.title}
      width={500}
      height={400}
      className="object-cover w-full h-64 transition-opacity duration-300"
      style={{ opacity: 1 }}
    />
  </div>
);

export default ImageCard;
