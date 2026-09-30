xcode-select --install
brew install python

git clone https://github.com/codi639/PET
cd PET

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m app.main --web
You may be prompted for permissions on first key read and store from PET.