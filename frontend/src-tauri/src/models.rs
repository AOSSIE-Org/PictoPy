use std::path::PathBuf;

pub struct FileInfo {
    pub path: PathBuf,
    pub file_type: FileType,
}

pub enum FileType {
    Image,
    Video,
    Other,
}