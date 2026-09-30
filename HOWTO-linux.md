```
sudo apt update
sudo apt install python3 python3-venv python3-pip gnome-keyring libsecret-1-0 git # Please make sure you're using at least 3.9. PET isn't tested under 3.12 but should still work over 3.9.

git clone https://github.com/codi639/PET
cd PET

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m app.main --web
```