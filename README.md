# IF Clubes

Aplicação Web em Flask com banco de dados MySQL.

## Preparar o ambiente

Abra o Prompt de Comando (`cmd`) na pasta do projeto e crie o ambiente virtual:

```bat
python -m venv .venv
```

Ative o ambiente e instale as dependências:

```cmd
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

No início de `app.py`, informe sua senha do MySQL n. A conexão está configurada para MySQL local (`localhost`), porta `3306`, usuário `root` e banco `if_clubes`.

No MySQL Workbench, abra e execute `schema.sql` para criar o banco e suas tabelas. Não compartilhe nem publique o `app.py` com sua senha real.

## Executar

Com o ambiente virtual ativado e na pasta do projeto, rode:

```bat
flask run
```

Se o comando `flask` não for encontrado, use:

```bat
python -m flask run
```

A aplicação ficará disponível em `http://127.0.0.1:5000`. Para verificar a conexão com o banco, abra `http://127.0.0.1:5000/health/db`.

O sistema oferece cadastro em `/cadastro`, login em `/login`, clubes em `/clubes`, eventos em `/eventos`, publicações e comentários nas páginas dos clubes e cadastro de eventos em `/eventos/novo` para responsáveis.
