@echo off
cd ..\python
python main.py ..\json\api-docs.yaml

echo.
echo Report generated. Press any key to open the HTML report...
pause >nul
start ..\html\rest_report.html