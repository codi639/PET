```
# Please make sure you're using at least 3.9. PET isn't tested under 3.12 but should still work over 3.9.
git clone https://github.com/codi639/PET
cd PET

py -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m app.main --web
```
If script execution is blocked:
``Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned``