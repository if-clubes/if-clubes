# IF Clubes

Aplicação Web em Flask com banco de dados MySQL.

## Preparar o ambiente

Na pasta do projeto, crie o ambiente virtual:

```
python -m venv .venv
```

No PowerShell, ative o ambiente e instale as dependências:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No Prompt de Comando (`cmd`), use:

```bat
.venv\Scripts\activate.bat
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

## Executar com Flask

Com o ambiente virtual ativado e as dependências instaladas, na raiz do projeto, execute:

```
flask run --debug
```

O Flask detecta automaticamente a instância `app` em `app.py`. A aplicação ficará disponível em `http://127.0.0.1:5000`. Se o comando `flask` não for encontrado, confirme que o ambiente virtual está ativado; também é possível iniciar com `python -m flask run --debug`.

A página inicial ficará disponível em `http://127.0.0.1:5000`. O sistema oferece cadastro em `/cadastro`, login em `/login`, saída em `/logout`, busca, participação e gerenciamento dos próprios clubes em `/clubes`, publicações e comentários na página de cada clube, eventos e confirmação de presença em `/eventos`, cadastro de eventos para responsáveis em `/eventos/novo` e verificação da conexão com o banco em `/health/db`.
