import os
from datetime import datetime

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or os.urandom(32)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="labinfo",
        database="if_clubes",
        connection_timeout=3,
    )


@app.get("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None
    email = request.form.get("email", "").strip().lower()

    if request.method == "POST":
        password = request.form.get("senha", "")
        if not email or not password:
            error_message = "Informe seu e-mail e sua senha."
        else:
            connection = None
            cursor = None
            try:
                connection = get_db_connection()
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT id, nome, email, senha_hash, tipo "
                    "FROM usuarios WHERE email = %s",
                    (email,),
                )
                user = cursor.fetchone()
                if user and check_password_hash(user[3], password):
                    session.clear()
                    session["usuario_id"] = user[0]
                    session["nome"] = user[1]
                    session["tipo"] = user[4]
                    return redirect(url_for("index"))
                error_message = "E-mail ou senha incorretos."
            except mysql.connector.Error:
                app.logger.exception("Falha ao autenticar usuário")
                error_message = "Não foi possível conectar ao banco de dados."
            finally:
                if cursor is not None:
                    cursor.close()
                if connection is not None and connection.is_connected():
                    connection.close()

    status_code = 200 if request.method == "GET" else 400
    if error_message == "E-mail ou senha incorretos.":
        status_code = 401
    if error_message == "Não foi possível conectar ao banco de dados.":
        status_code = 503
    return render_template("login.html", error_message=error_message, email=email), status_code


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.get("/clubes/<int:club_id>")
def club_detail(club_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT clubes.id, clubes.nome, clubes.descricao, clubes.categoria, "
            "clubes.local, clubes.horarios, clubes.responsavel_id, "
            "usuarios.nome AS responsavel "
            "FROM clubes JOIN usuarios ON usuarios.id = clubes.responsavel_id "
            "WHERE clubes.id = %s",
            (club_id,),
        )
        club = cursor.fetchone()
        if club is None:
            return "Clube não encontrado.", 404

        cursor.execute(
            "SELECT publicacoes.id, publicacoes.conteudo, publicacoes.criado_em, "
            "usuarios.nome AS autor "
            "FROM publicacoes JOIN usuarios ON usuarios.id = publicacoes.autor_id "
            "WHERE publicacoes.clube_id = %s ORDER BY publicacoes.criado_em DESC",
            (club_id,),
        )
        posts = cursor.fetchall()
        cursor.execute(
            "SELECT comentarios.publicacao_id, comentarios.conteudo, "
            "comentarios.criado_em, usuarios.nome AS autor "
            "FROM comentarios JOIN usuarios ON usuarios.id = comentarios.autor_id "
            "JOIN publicacoes ON publicacoes.id = comentarios.publicacao_id "
            "WHERE publicacoes.clube_id = %s ORDER BY comentarios.criado_em",
            (club_id,),
        )
        comments_by_post = {post["id"]: [] for post in posts}
        for comment in cursor.fetchall():
            comments_by_post[comment["publicacao_id"]].append(comment)

        return render_template(
            "clube_detalhe.html",
            clube=club,
            publicacoes=posts,
            comentarios_por_publicacao=comments_by_post,
        )
    except mysql.connector.Error:
        app.logger.exception("Falha ao carregar página do clube")
        return "Não foi possível carregar o clube agora.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.post("/clubes/<int:club_id>/publicacoes")
def create_post(club_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))
    if session.get("tipo") != "responsavel":
        return "Somente responsáveis podem publicar no clube.", 403

    content = request.form.get("conteudo", "").strip()
    if not content or len(content) > 5000:
        return "A publicação deve ter entre 1 e 5000 caracteres.", 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM clubes WHERE id = %s AND responsavel_id = %s",
            (club_id, session["usuario_id"]),
        )
        if cursor.fetchone() is None:
            return "Clube não encontrado.", 404
        cursor.execute(
            "INSERT INTO publicacoes (conteudo, autor_id, clube_id) "
            "VALUES (%s, %s, %s)",
            (content, session["usuario_id"], club_id),
        )
        connection.commit()
        return redirect(url_for("club_detail", club_id=club_id))
    except mysql.connector.Error:
        app.logger.exception("Falha ao criar publicação")
        return "Não foi possível publicar agora.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.post("/publicacoes/<int:post_id>/comentarios")
def create_comment(post_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))

    content = request.form.get("conteudo", "").strip()
    if not content or len(content) > 1500:
        return "O comentário deve ter entre 1 e 1500 caracteres.", 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT clube_id FROM publicacoes WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        if post is None:
            return "Publicação não encontrada.", 404
        cursor.execute(
            "INSERT INTO comentarios (conteudo, autor_id, publicacao_id) "
            "VALUES (%s, %s, %s)",
            (content, session["usuario_id"], post_id),
        )
        connection.commit()
        return redirect(url_for("club_detail", club_id=post[0]))
    except mysql.connector.Error:
        app.logger.exception("Falha ao criar comentário")
        return "Não foi possível comentar agora.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.get("/eventos")
def list_events():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT eventos.id, eventos.nome, eventos.descricao, eventos.data_hora, "
            "eventos.local, clubes.nome AS clube, "
            "(SELECT COUNT(*) FROM presencas_eventos "
            "WHERE presencas_eventos.evento_id = eventos.id) AS total_confirmados, "
            "EXISTS (SELECT 1 FROM presencas_eventos "
            "WHERE presencas_eventos.evento_id = eventos.id "
            "AND presencas_eventos.usuario_id = %s) AS usuario_confirmou "
            "FROM eventos JOIN clubes ON clubes.id = eventos.clube_id "
            "ORDER BY eventos.data_hora",
            (session.get("usuario_id", 0),),
        )
        events = cursor.fetchall()
        return render_template("eventos.html", eventos=events)
    except mysql.connector.Error:
        app.logger.exception("Falha ao consultar eventos")
        return render_template(
            "eventos.html",
            eventos=[],
            error_message="Não foi possível carregar os eventos. Confira se o schema atualizado foi executado no Workbench.",
        ), 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/eventos/novo", methods=["GET", "POST"])
def create_event():
    if not session.get("usuario_id"):
        return redirect(url_for("login"))
    if session.get("tipo") != "responsavel":
        return "Somente responsáveis podem cadastrar eventos.", 403

    connection = None
    cursor = None
    event_name = request.form.get("nome", "").strip()
    description = request.form.get("descricao", "").strip()
    event_date = request.form.get("data_hora", "").strip()
    location = request.form.get("local", "").strip()
    selected_club = request.form.get("clube_id", "").strip()
    error_message = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nome FROM clubes WHERE responsavel_id = %s ORDER BY nome",
            (session["usuario_id"],),
        )
        clubes = cursor.fetchall()
        owned_club_ids = {str(club["id"]) for club in clubes}

        if request.method == "POST":
            if not event_name or len(event_name) > 120:
                error_message = "Informe um nome com até 120 caracteres."
            elif not description or len(description) > 5000:
                error_message = "Informe uma descrição com até 5000 caracteres."
            elif not location or len(location) > 180:
                error_message = "Informe um local com até 180 caracteres."
            elif selected_club not in owned_club_ids:
                error_message = "Selecione um clube que você administra."
            else:
                try:
                    parsed_date = datetime.strptime(event_date, "%Y-%m-%dT%H:%M")
                    if parsed_date <= datetime.now():
                        error_message = "A data do evento deve estar no futuro."
                except ValueError:
                    error_message = "Informe uma data e horário válidos."

            if request.method == "POST" and not error_message:
                cursor.execute(
                    "INSERT INTO eventos (nome, descricao, data_hora, local, clube_id) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (event_name, description, parsed_date, location, int(selected_club)),
                )
                connection.commit()
                return redirect(url_for("list_events"))

        status_code = 400 if error_message else 200
        return render_template(
            "evento_novo.html",
            clubes=clubes,
            sem_clubes=not clubes,
            error_message=error_message,
            nome=event_name,
            descricao=description,
            data_hora=event_date,
            local=location,
            clube_selecionado=selected_club,
        ), status_code
    except mysql.connector.Error:
        app.logger.exception("Falha ao cadastrar evento")
        return "Não foi possível carregar ou salvar o evento no banco de dados.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.post("/eventos/<int:event_id>/confirmar")
def confirm_event_presence(event_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM eventos WHERE id = %s", (event_id,))
        if cursor.fetchone() is None:
            return "Evento não encontrado.", 404
        cursor.execute(
            "INSERT IGNORE INTO presencas_eventos (usuario_id, evento_id) "
            "VALUES (%s, %s)",
            (session["usuario_id"], event_id),
        )
        connection.commit()
        return redirect(url_for("list_events"))
    except mysql.connector.Error:
        app.logger.exception("Falha ao confirmar presença no evento")
        return "Não foi possível confirmar presença agora.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.post("/eventos/<int:event_id>/cancelar-presenca")
def cancel_event_presence(event_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM presencas_eventos WHERE usuario_id = %s AND evento_id = %s",
            (session["usuario_id"], event_id),
        )
        connection.commit()
        return redirect(url_for("list_events"))
    except mysql.connector.Error:
        app.logger.exception("Falha ao cancelar presença no evento")
        return "Não foi possível cancelar presença agora.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.get("/clubes")
def list_clubs():
    connection = None
    cursor = None
    search_term = request.args.get("q", "").strip()
    selected_category = request.args.get("categoria", "").strip()
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = (
            "SELECT clubes.id, clubes.responsavel_id, clubes.nome, clubes.descricao, clubes.categoria, "
            "clubes.local, clubes.horarios, usuarios.nome AS responsavel, "
            "(SELECT COUNT(*) FROM membros_clubes "
            "WHERE membros_clubes.clube_id = clubes.id) AS total_membros, "
            "EXISTS (SELECT 1 FROM membros_clubes "
            "WHERE membros_clubes.clube_id = clubes.id AND membros_clubes.usuario_id = %s) "
            "AS usuario_participa "
            "FROM clubes JOIN usuarios ON usuarios.id = clubes.responsavel_id "
        )
        parameters = [session.get("usuario_id", 0)]
        filters = []
        if search_term:
            filters.append(
                "(clubes.nome LIKE %s OR clubes.descricao LIKE %s "
                "OR clubes.categoria LIKE %s)"
            )
            search_pattern = f"%{search_term}%"
            parameters.extend([search_pattern, search_pattern, search_pattern])
        if selected_category:
            filters.append("clubes.categoria = %s")
            parameters.append(selected_category)
        if filters:
            query += "WHERE " + " AND ".join(filters) + " "
        query += "ORDER BY clubes.nome"
        cursor.execute(query, tuple(parameters))
        clubs = cursor.fetchall()
        cursor.execute("SELECT DISTINCT categoria FROM clubes ORDER BY categoria")
        categories = [row["categoria"] for row in cursor.fetchall()]
        return render_template(
            "clubes.html",
            clubes=clubs,
            categorias=categories,
            termo=search_term,
            categoria_selecionada=selected_category,
        )
    except mysql.connector.Error:
        app.logger.exception("Falha ao consultar clubes")
        return render_template(
            "clubes.html",
            clubes=[],
            categorias=[],
            termo=search_term,
            categoria_selecionada=selected_category,
            error_message="Não foi possível carregar os clubes. Confira se o schema atualizado foi executado no Workbench.",
        ), 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.post("/clubes/<int:club_id>/participar")
def join_club(club_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM clubes WHERE id = %s", (club_id,))
        if cursor.fetchone() is None:
            return "Clube não encontrado.", 404
        cursor.execute(
            "INSERT IGNORE INTO membros_clubes (usuario_id, clube_id) "
            "VALUES (%s, %s)",
            (session["usuario_id"], club_id),
        )
        connection.commit()
        return redirect(url_for("list_clubs"))
    except mysql.connector.Error:
        app.logger.exception("Falha ao participar do clube")
        return "Não foi possível participar do clube agora.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.post("/clubes/<int:club_id>/sair")
def leave_club(club_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM membros_clubes WHERE usuario_id = %s AND clube_id = %s",
            (session["usuario_id"], club_id),
        )
        connection.commit()
        return redirect(url_for("list_clubs"))
    except mysql.connector.Error:
        app.logger.exception("Falha ao sair do clube")
        return "Não foi possível sair do clube agora.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/clubes/<int:club_id>/editar", methods=["GET", "POST"])
def edit_club(club_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))
    if session.get("tipo") != "responsavel":
        return "Somente responsáveis podem editar clubes.", 403

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT nome, descricao, categoria, local, horarios "
            "FROM clubes WHERE id = %s AND responsavel_id = %s",
            (club_id, session["usuario_id"]),
        )
        club = cursor.fetchone()
        if club is None:
            return "Clube não encontrado.", 404

        name = request.form.get("nome", club["nome"]).strip()
        description = request.form.get("descricao", club["descricao"]).strip()
        category = request.form.get("categoria", club["categoria"]).strip()
        location = request.form.get("local", club["local"]).strip()
        schedule = request.form.get("horarios", club["horarios"]).strip()
        error_message = None

        if request.method == "POST":
            if not name or len(name) > 120:
                error_message = "Informe um nome com até 120 caracteres."
            elif not description or len(description) > 5000:
                error_message = "Informe uma descrição com até 5000 caracteres."
            elif not category or len(category) > 80:
                error_message = "Informe uma categoria com até 80 caracteres."
            elif not location or len(location) > 180:
                error_message = "Informe um local com até 180 caracteres."
            elif not schedule or len(schedule) > 180:
                error_message = "Informe os horários com até 180 caracteres."
            else:
                cursor.execute(
                    "UPDATE clubes SET nome = %s, descricao = %s, categoria = %s, "
                    "local = %s, horarios = %s "
                    "WHERE id = %s AND responsavel_id = %s",
                    (
                        name,
                        description,
                        category,
                        location,
                        schedule,
                        club_id,
                        session["usuario_id"],
                    ),
                )
                connection.commit()
                return redirect(url_for("list_clubs"))

        return render_template(
            "clube_novo.html",
            error_message=error_message,
            nome=name,
            descricao=description,
            categoria=category,
            local=location,
            horarios=schedule,
            clube_id=club_id,
        ), 400 if error_message else 200
    except mysql.connector.Error:
        app.logger.exception("Falha ao editar clube")
        return "Não foi possível carregar ou salvar o clube.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.post("/clubes/<int:club_id>/excluir")
def delete_club(club_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))
    if session.get("tipo") != "responsavel":
        return "Somente responsáveis podem excluir clubes.", 403

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM clubes WHERE id = %s AND responsavel_id = %s",
            (club_id, session["usuario_id"]),
        )
        if cursor.rowcount == 0:
            return "Clube não encontrado.", 404
        connection.commit()
        return redirect(url_for("list_clubs"))
    except mysql.connector.Error:
        app.logger.exception("Falha ao excluir clube")
        return "Não foi possível excluir o clube agora.", 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/clubes/novo", methods=["GET", "POST"])
def create_club():
    if not session.get("usuario_id"):
        return redirect(url_for("login"))
    if session.get("tipo") != "responsavel":
        return "Somente responsáveis por clubes podem cadastrar clubes.", 403

    error_message = None
    name = request.form.get("nome", "").strip()
    description = request.form.get("descricao", "").strip()
    category = request.form.get("categoria", "").strip()
    location = request.form.get("local", "").strip()
    schedule = request.form.get("horarios", "").strip()

    if request.method == "POST":
        if not name or len(name) > 120:
            error_message = "Informe um nome com até 120 caracteres."
        elif not description or len(description) > 5000:
            error_message = "Informe uma descrição com até 5000 caracteres."
        elif not category or len(category) > 80:
            error_message = "Informe uma categoria com até 80 caracteres."
        elif not location or len(location) > 180:
            error_message = "Informe um local com até 180 caracteres."
        elif not schedule or len(schedule) > 180:
            error_message = "Informe os horários com até 180 caracteres."
        else:
            connection = None
            cursor = None
            try:
                connection = get_db_connection()
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO clubes "
                    "(nome, descricao, categoria, local, horarios, responsavel_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        name,
                        description,
                        category,
                        location,
                        schedule,
                        session["usuario_id"],
                    ),
                )
                connection.commit()
                return redirect(url_for("list_clubs"))
            except mysql.connector.Error:
                app.logger.exception("Falha ao cadastrar clube")
                error_message = "Não foi possível salvar o clube no banco de dados."
            finally:
                if cursor is not None:
                    cursor.close()
                if connection is not None and connection.is_connected():
                    connection.close()

    status_code = 400 if error_message else 200
    if error_message == "Não foi possível salvar o clube no banco de dados.":
        status_code = 503
    return render_template(
        "clube_novo.html",
        error_message=error_message,
        nome=name,
        descricao=description,
        categoria=category,
        local=location,
        horarios=schedule,
        clube_id=None,
    ), status_code


@app.route("/cadastro", methods=["GET", "POST"])
def register_user():
    error_message = None
    success_message = None
    name = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    user_type = request.form.get("tipo", "aluno").strip()

    if request.method == "POST":
        password = request.form.get("senha", "")
        if not name or len(name) > 120:
            error_message = "Informe um nome com até 120 caracteres."
        elif not email or len(email) > 254 or "@" not in email:
            error_message = "Informe um e-mail válido."
        elif len(password) < 8:
            error_message = "A senha deve ter pelo menos 8 caracteres."
        elif user_type not in ("aluno", "responsavel"):
            error_message = "Selecione um tipo de usuário válido."
        else:
            connection = None
            cursor = None
            try:
                connection = get_db_connection()
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (nome, email, senha_hash, tipo) "
                    "VALUES (%s, %s, %s, %s)",
                    (name, email, generate_password_hash(password), user_type),
                )
                connection.commit()
                success_message = "Cadastro realizado com sucesso."
                name = ""
                email = ""
                user_type = "aluno"
            except mysql.connector.IntegrityError as error:
                if error.errno == 1062:
                    error_message = "Este e-mail já está cadastrado."
                else:
                    app.logger.exception("Falha ao cadastrar usuário")
                    error_message = "Não foi possível concluir o cadastro agora."
            except mysql.connector.Error:
                app.logger.exception("Falha ao cadastrar usuário")
                error_message = "Não foi possível conectar ao banco de dados."
            finally:
                if cursor is not None:
                    cursor.close()
                if connection is not None and connection.is_connected():
                    connection.close()

    status_code = 400 if error_message else 200
    if error_message == "Este e-mail já está cadastrado.":
        status_code = 409
    elif error_message == "Não foi possível conectar ao banco de dados.":
        status_code = 503

    return render_template(
        "cadastro.html",
        error_message=error_message,
        success_message=success_message,
        nome=name,
        email=email,
        tipo=user_type,
    ), status_code


@app.get("/health/db")
def database_health():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return jsonify(status="ok", database="connected")
    except mysql.connector.Error:
        app.logger.exception("Falha ao verificar a conexão com o MySQL")
        return jsonify(status="error", message="Não foi possível conectar ao MySQL."), 503
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    app.run(debug=True)