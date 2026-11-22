import { FolderDetails, countSubfolders } from '../Folder';

const folder = (id: string, parent?: string): FolderDetails => ({
  folder_id: id,
  folder_path: `/${id}`,
  parent_folder_id: parent,
  last_modified_time: 0,
  AI_Tagging: false,
});

describe('countSubfolders', () => {
  const folders = [
    folder('root'),
    folder('a', 'root'),
    folder('b', 'a'),
    folder('c', 'a'),
    folder('other'),
  ];

  test('counts every level below the folder', () => {
    expect(countSubfolders(folders, 'root')).toBe(3);
    expect(countSubfolders(folders, 'a')).toBe(2);
  });

  test('is zero for a leaf or an unknown id', () => {
    expect(countSubfolders(folders, 'b')).toBe(0);
    expect(countSubfolders(folders, 'other')).toBe(0);
    expect(countSubfolders(folders, 'missing')).toBe(0);
  });
});
