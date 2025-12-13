export interface RepresentativeMedia {
  id: string;
  thumbnailPath: string;
}

export interface DateRange {
  start: string;
  end: string;
}

export interface Memory {
  id: string;
  title: string;
  type: string; // "on_this_day", "trip", "date_cluster", etc.
  date_range: DateRange;
  location: string | null;
  media_count: number;
  representative_media: RepresentativeMedia[];
  media_ids: string[];
}
