## Setting Up using Script

### Video Setup Guide:

- [Windows](https://youtu.be/nNVAE4or280?si=j_y9Xn8Kra6tPHjw)
- [Ubuntu (Debian)](https://www.youtube.com/watch?v=a7I0ZRE-SHk)

### Prerequisites:

- [NodeJS](https://nodejs.org/en) (LTS Version Recommended)
- [Git](https://git-scm.com/downloads) version control system

### Steps Performed in the Video:

1. Fork the PictoPy repository: https://github.com/AOSSIE-Org/PictoPy

2. Open your terminal (or Powershell with administrator privileges on Windows)

3. Clone your forked repository:

   ```bash
   git clone https://github.com/yourUsername/PictoPy
   ```

4. Change to the repository directory:

   ```bash
   cd PictoPy
   ```

5. Add the main repository as "upstream":

   ```bash
   git remote add upstream https://github.com/AOSSIE-Org/PictoPy
   ```

6. Run the Automatic Setup

   ```bash
   npm run setup
   ```

   > **Note:** This step can take a long time depending on your internet connection and system specifications. If the script seems to stop progressing after waiting for more than 10 minutes, press Enter in your terminal window to continue.

7. Start the Backend Server

   #### Windows

   ```powershell
   cd .\backend
   .env\Scripts\activate.ps1
   fastapi dev
   ```

   #### Linux

   ```bash
   cd ./backend
   source .env/bin/activate
   fastapi dev
   ```

8. Start the Frontend Desktop App

   Open a new terminal window, navigate to the project directory, and run:

   ```bash
   cd frontend
   npm run tauri dev
   ```

9. Pre-commit Setup

   Before running the `git commit` command, ensure you have the following Python packages installed globally:

   ```bash
   pip install ruff black mypy pre-commit
   ```

   > **Note:** If you are committing from a virtual environment, these packages should already be installed as they are included in the requirements.txt file.
