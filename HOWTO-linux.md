sudo apt update
sudo apt install python3 python3-venv python3-pip gnome-keyring libsecret-1-0 git

git clone https://github.com/codi639/PET
cd PET

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m app.main --web