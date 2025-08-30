# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Install dependencies 
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
    librsvg2-dev \
    file \
    nsis \
    lld \
    llvm \
    clang \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Node.js (Node.js 16 is compatible with Tauri)
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs

# Install Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Tauri CLI
RUN npm install -g @tauri-apps/cli

# Define build arguments
ARG TAURI_SIGNING_PRIVATE_KEY
ARG TAURI_SIGNING_PRIVATE_KEY_PASSWORD

#Setting up Windows Rust target
RUN rustup target add x86_64-pc-windows-msvc
RUN cargo install --locked cargo-xwin

# Copy the application source code to the container
WORKDIR /app

# Copy the package.json file
COPY package.json .

# Install dependencies
RUN npm install

# Copy the rest of the code
COPY . .

# Set environment variables using build arguments
ENV TAURI_SIGNING_PRIVATE_KEY=$TAURI_SIGNING_PRIVATE_KEY
ENV TAURI_SIGNING_PRIVATE_KEY_PASSWORD=$TAURI_SIGNING_PRIVATE_KEY_PASSWORD

# Set the container's entrypoint to access the bundled files
EXPOSE 1420
CMD ["tail", "-f" ,"/dev/null"]
