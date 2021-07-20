if ( -not (Test-Path -Path 'venv' -PathType Container) ) {
    python3 -m venv venv
}
venv/bin/Activate.ps1

pip3 install -r requirements.txt
