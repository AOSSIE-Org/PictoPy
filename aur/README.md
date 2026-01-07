# PictoPy AUR Package

This directory contains the files needed to publish PictoPy to the [Arch User Repository (AUR)](https://aur.archlinux.org/).

## Package Variants

### `pictopy` (Binary Package)
The main package that installs pre-built binaries from GitHub releases. This is the recommended option for most users.

### `pictopy-git` (Source Package)
Builds PictoPy from the latest git source. Use this if you want the bleeding-edge version or need to make modifications.

## Installation

### Using an AUR Helper (Recommended)

```bash
# Using yay
yay -S pictopy

# Using paru
paru -S pictopy

# Using pikaur
pikaur -S pictopy
```

### Manual Installation

```bash
# Clone the AUR repository
git clone https://aur.archlinux.org/pictopy.git
cd pictopy

# Build and install
makepkg -si
```

### Installing from Git Source

```bash
# Using yay
yay -S pictopy-git

# Or manually
git clone https://aur.archlinux.org/pictopy-git.git
cd pictopy-git
makepkg -si
```

## Dependencies

### Runtime Dependencies
- `webkit2gtk-4.1` - WebKit rendering engine
- `gtk3` - GTK+ 3 toolkit
- `glib2` - GLib library
- `cairo` - 2D graphics library
- `pango` - Text rendering
- `gdk-pixbuf2` - Image loading
- `libsoup3` - HTTP library
- `openssl` - Cryptography
- `hicolor-icon-theme` - Icon theme

### Optional Dependencies
- `python-onnxruntime` - For AI model inference
- `python-opencv` - For image processing
- `python-numpy` - For numerical operations

## Updating the AUR Package

The package is automatically updated via GitHub Actions when a new release is published. To manually update:

1. Update the `pkgver` in `PKGBUILD`
2. Update the source URLs if needed
3. Regenerate checksums: `updpkgsums`
4. Regenerate `.SRCINFO`: `makepkg --printsrcinfo > .SRCINFO`
5. Commit and push to AUR

## GitHub Actions Setup

To enable automatic AUR publishing, add these secrets to your GitHub repository:

- `AUR_USERNAME` - Your AUR username
- `AUR_EMAIL` - Your AUR email
- `AUR_SSH_PRIVATE_KEY` - SSH private key registered with AUR

### Generating SSH Key for AUR

```bash
# Generate a new SSH key
ssh-keygen -t ed25519 -C "your-email@example.com" -f aur_key

# Add the public key to your AUR account
cat aur_key.pub
# Copy this to: https://aur.archlinux.org/account/YOUR_USERNAME/edit

# Add the private key as a GitHub secret (AUR_SSH_PRIVATE_KEY)
cat aur_key
```

## Troubleshooting

### Build Fails with Missing Dependencies
```bash
# Install all build dependencies
sudo pacman -S --needed base-devel rust cargo nodejs npm python python-pip webkit2gtk-4.1
```

### Application Won't Start
```bash
# Check for missing libraries
ldd /usr/bin/pictopy | grep "not found"

# Install missing dependencies
sudo pacman -S webkit2gtk-4.1 gtk3
```

### AI Features Not Working
```bash
# Install optional AI dependencies
sudo pacman -S python-onnxruntime python-opencv python-numpy
```

## License

MIT License - See the main repository for details.
