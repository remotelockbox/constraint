if ( Test-Path -Path 'venv' -PathType Container) {
    venv/bin/Activate.ps1
}
python3 run.py

