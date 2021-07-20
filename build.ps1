if ( -not (Test-Path -Path 'venv' -PathType Container) ) {
    py -m venv venv
}

. venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt

Read-Host -Prompt "Press Enter to exit"
