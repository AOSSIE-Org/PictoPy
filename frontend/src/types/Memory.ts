export type MemoryType = 'DAY' | 'TRIP' | 'YEAR' | 'LOCATION';

export interface Memory {
  id: string;

  /**
   * Type of memory
   * DAY      → On this day
   * TRIP     → Trip to Jaipur, 2023
   * YEAR     → Memories from 2024
   * LOCATION → Pune, Amravati, etc.
   */
  type: MemoryType;

  /** Main title shown on the card */
  title: string;

  /** Optional subtitle (date range, year, etc.) */
  subtitle?: string;

  /** Image IDs associated with this memory */
  image_ids: string[];

  /** Optional metadata (future-safe) */
  created_at?: string;
}
