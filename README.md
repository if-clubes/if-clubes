# IF Clubes

Aplicação Web em Flask com banco de dados MySQL.

## Preparar o ambiente

No PowerShell, na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Crie ou edite `.env` na raiz do projeto com as credenciais locais do MySQL e uma chave para as sessões:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha_do_mysql
MYSQL_DATABASE=if_clubes
SECRET_KEY=uma_chave_secreta_aleatoria
```

Gere uma chave aleatória com `python -c "import secrets; print(secrets.token_hex(32))"`. No MySQL Workbench, abra e execute `schema.sql` para criar o banco `if_clubes`, usuários, clubes, membros, eventos, presenças, publicações e comentários.

A página inicial ficará disponível em `http://127.0.0.1:5000`. O sistema oferece cadastro em `/cadastro`, login em `/login`, saída em `/logout`, busca, participação e gerenciamento dos próprios clubes em `/clubes`, publicações e comentários na página de cada clube, eventos e confirmação de presença em `/eventos`, cadastro de eventos para responsáveis em `/eventos/novo` e verificação da conexão com o banco em `/health/db`.
