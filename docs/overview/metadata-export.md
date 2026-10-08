# Metadata Export

Everything PictoPy works out about your photos — the tags, the faces and who they belong to, the embeddings behind semantic search — is the result of running AI models on your own machine. That takes time and processing power.

Metadata export writes those results **into the photo files themselves**, so they travel with your photos. The goal is that if you reinstall PictoPy, move to a new computer, or remove a photo and add it back, the work does not have to be redone from scratch.

!!! note "Reading the metadata back is not built yet"
    Today PictoPy only **writes** this metadata. A future version will read it when photos are imported and reuse it instead of running the models again. Until then, exported metadata does not speed up a reinstall.

## What gets saved

| Saved in the photo | Notes |
| --- | --- |
| AI tags | Objects detected in the photo, such as "person" or "dog" |
| Semantic tags | With the confidence score behind each one |
| Faces | Where each face is, its face embedding, and the name of the person, if you have named them |
| Image embedding | The one semantic search uses, with the model that produced it |
| Favourite | Whether you starred the photo |
| Albums | The names of the albums the photo is in — **except locked albums** |
| Image size | Width and height, so a later reader can tell if the photo was cropped since |
| Model versions | Which face model and which semantic vocabulary produced the data |

Faces in a person group you have not named are saved without a name.

## Only PNG photos, for now

Metadata is currently written to **PNG** files only. JPEG, HEIC, WebP and every other format are never touched.

Your photo is not re-saved or re-compressed. PictoPy adds a separate metadata block to the file and leaves the image data byte-for-byte as it was, so the picture itself cannot lose quality.

## Turning it on

Open **Settings → Image Metadata**.

- **Save Metadata Automatically** — off by default, because it changes your original files. Turn it on and PictoPy keeps the files up to date by itself, as described below. A few seconds after you turn it on, PictoPy starts catching up the whole library.
- **Export Now** — the **Export metadata** button checks every PNG photo in the library right away, whether or not the automatic setting is on, and writes any whose saved metadata is missing or out of date. Photos that are already up to date are left untouched. The line next to it tells you how many PNG photos still need their metadata saved; it updates while an export is running.

## When automatic export runs

With **Save Metadata Automatically** on, PictoPy writes metadata:

- **After tagging.** Once the photo stages of processing finish (objects, faces, people, embeddings, semantic tags), and before videos are processed.
- **A few seconds after you edit something** that is saved in the photo: marking a favourite, adding photos to an album or removing them, creating an album from a memory, renaming, locking, unlocking or deleting an album, renaming a person, or regrouping people. Edits made in quick succession are written together once you pause.
- **When PictoPy starts**, for anything left over from last time.
- **After the semantic search models are installed**, once their embeddings and tags exist.

## Photos are only rewritten when something changed

PictoPy keeps track of which photos have new information to save. A photo is only rewritten when its saved metadata would actually be different, and when PictoPy already knows a file is up to date it does not even open it. Favouriting a photo and then un-favouriting it, for example, leaves the file untouched.

A photo with nothing worth saving (not tagged, not a favourite, in no album) is not written at all. If a photo that was written before ends up with nothing to save — say it was a favourite and no longer is — its file is updated to match.

If a new version of PictoPy saves more information, or saves it differently, automatic export updates each photo only as that photo changes. To bring all your exported photos up to date at once, use **Export metadata**.

## Your file dates stay the same

Writing metadata changes a file's size, but PictoPy puts the file's **modified date** back to what it was. For a photo whose EXIF data has no capture date, PictoPy uses that modified date as the photo's date, so keeping it keeps the photo where it was.

PictoPy also records the new file size, so the next folder scan recognises the file as unchanged and does not process it again.

## If a photo cannot be written

A photo that cannot be written — on a drive that is not plugged in, in a read-only folder, or open in another program — does not stop the rest. PictoPy tries again on the next export, and the **Export Now** line shows how many photos are waiting to be retried.

PictoPy also deliberately leaves two kinds of file alone:

- a file whose existing metadata (written by another program) it cannot read, because rewriting it could destroy that metadata;
- a file whose metadata was written by a newer version of PictoPy.

Automatic export leaves them alone until the photo changes again. **Export metadata** checks them again.

## Privacy

Metadata export only writes to files on your machine; nothing is uploaded. Three things are worth knowing:

- **Locked albums are never written into a photo.** Their names stay in PictoPy only.
- **Shared albums never include this metadata.** When someone opens an album you [share](sharing-albums.md), PictoPy removes its metadata from each photo as it sends it — the face data and names never reach them. Metadata from other programs, such as camera EXIF, is sent as usual.
- **Copying a file yourself copies its metadata.** A PNG you email, upload or copy to a USB stick carries the faces, names and album names saved in it. That is what lets the metadata survive a reinstall, but it means the file says more than the picture does.

## Limitations

- PNG files only.
- Writing only; PictoPy does not read this metadata back yet.
- Groups of faces you have not named are saved as faces without a name, not as a group.
- If a file is open in another program while PictoPy writes to it, Windows may refuse the write; PictoPy retries on the next export.
- The modified date is kept, but on Windows the file's **created** date changes when it is written, because PictoPy replaces the file in one step so a crash can never leave it half-written. PictoPy itself does not use the created date.

## For developers

How the metadata is stored, how PictoPy tracks what needs exporting, and how sharing removes it are documented in [Metadata Export internals](../backend/backend_python/metadata-export.md).
