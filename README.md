# rocktea-mall-api
RockTea Mall: Your dropshipping platform for custom domains, product selection, and seamless e-commerce. Start your business effortlessly.

## create a new virtual environment
```bash
py -3 -m venv .venv
```

## to activate python virtual environment
```bash
.venv\Scripts\activate
```

## install requirements from requirements.txt
```bash
pip install -r ./main/requirements.txt
```

## to leave the virtual environment
```bash
deactivate
```

## to run migration
```bash
python ./main/manage.py makemigrations
python ./main/manage.py migrate
```

## to start python app
```bash
python ./main/manage.py runserver
```

## upgrade pip inside the environment
```bash
python -m pip install --upgrade pip
```

## find last migrtion for a specif app
```bash
python ./main/manage.py showmigrations mall
```

## rollback last migration
```bash
python ./main/manage.py migrate mall 0049_customuser_is_verified
```

## delete migration file
```bash
rm main/mall/migrations/0049_customuser_is_verified.py  # For Linux/macOS
del main\mall\migrations\0049_customuser_is_verified.py  # For Windows PowerShell
```