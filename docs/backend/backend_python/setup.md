# Python Backend Setup

## Setup Directory

!!! note "Base Directory"
All commands executed below are with respect to the `backend/` directory

### Installing requirments

We suggest setting up a virtual environment and run the following command

```bash
pip install -r requirements.txt
```

The entry point for backend is `main.py` , since PictoPy is built on top of FastAPI, we suggest using the `run` scripts which are available in both
`.bat` and `.sh` formats.

!!! note "UNIX Development"
For UNIX based systems, to run in development mode run
`bash
    ./run.sh --test
    `
The backend should now be successfully running on port 8000 by default. To change this modify the start-up scripts.
