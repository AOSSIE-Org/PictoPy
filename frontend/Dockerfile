# Use Ubuntu 22.04 as base for newer GLib version
FROM ubuntu:22.04

# Install dependencies (including GLib >= 2.70)
RUN apt-get update && \
    apt-get install -y \
        curl \
        build-essential \
        libgtk-3-dev \
        libwebkit2gtk-4.0-dev \
        libappindicator3-dev \
        wget \
        xz-utils \
        libssl-dev \
        libglib2.0-dev \
        libgirepository1.0-dev \
        pkg-config \
        software-properties-common \
        libjavascriptcoregtk-4.0-dev \
        libjavascriptcoregtk-4.1-dev \
        libsoup-3.0-dev \
        libwebkit2gtk-4.1-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set PKG_CONFIG_PATH environment variable
# ENV PKG_CONFIG_PATH=/usr/lib/x86_64-linux-gnu/pkgconfig

# Install Node.js (Node.js 16 is compatible with Tauri)
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs

# Install Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Tauri CLI
RUN npm install -g @tauri-apps/cli

# Copy the application source code to the container
WORKDIR /app
COPY . .

# Install dependencies
RUN npm install

ENV TAURI_SIGNING_PRIVATE_KEY=dW50cnVzdGVkIGNvbW1lbnQ6IHJzaWduIGVuY3J5cHRlZCBzZWNyZXQga2V5ClJXUlRZMEl5NlF2SjE3cWNXOVlQQ0JBTlNITEpOUVoyQ3ZuNTdOSkwyNE1NN2RmVWQ1a0FBQkFBQUFBQUFBQUFBQUlBQUFBQU9XOGpTSFNRd0Q4SjNSbm5Oc1E0OThIUGx6SS9lWXI3ZjJxN3BESEh1QTRiQXlkR2E5aG1oK1g0Tk5kcmFzc0IvZFZScEpubnptRkxlbDlUR2R1d1Y5OGRSYUVmUGoxNTFBcHpQZ1dSS2lHWklZVHNkV1Byd1VQSnZCdTZFWlVGOUFNVENBRlgweUU9Cg==
ENV TAURI_SIGNING_PRIVATE_KEY_PASSWORD=pass

# Build the frontend (React app)
RUN npm run build

# Build the Tauri application
RUN npm run tauri build -v

# Set the container's entrypoint to access the bundled files
CMD ["bash"]