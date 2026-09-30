```
xcode-select --install
brew install python # Please make sure you're using at least 3.9. PET isn't tested under 3.12 but should still work over 3.9.

git clone https://github.com/codi639/PET
cd PET

python3 -m venv .venv # Or python3.14 or any version you want
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m app.main --web
```
You may be prompted for permissions on first key read and store from PET.