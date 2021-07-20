if ( Test-Path -Path 'venv' -PathType Container) {
    . venv\Scripts\Activate.ps1
}

py run.py -m constraint.cli

Read-Host -Prompt "Press Enter to exit"
