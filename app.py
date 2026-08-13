# app.py
# Agenda Financeira - Giulia Neves
# Backend Flask: login, API de dados, persistência em dados.json e backup.

import json
import os

from flask import (Flask, jsonify, redirect, render_template, request,
                   send_file, session, url_for)

# Caminho absoluto: garante que dados.json fique SEMPRE na pasta do projeto,
# independentemente de onde o comando "python app.py" for executado.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "dados.json")

app = Flask(__name__)
# Em produção, prefira definir via variável de ambiente.
app.secret_key = os.environ.get("AGENDA_SECRET_KEY", "giulia-chave-secreta-020806")

# Credenciais de acesso inicial (podem vir de variáveis de ambiente)
USUARIO = os.environ.get("AGENDA_USUARIO", "Giulia")
SENHA = os.environ.get("AGENDA_SENHA", "020806")

# ---------- Persistência ----------
def dados_iniciais():
    """Seed usado na primeira execução (quando dados.json ainda não existe)."""
    return {
        "movimentacoes": [
            {"id": 1, "desc": "Salário Mensal", "valor": 5500, "tipo": "receita", "cat": "Renda", "mes": "2026-08"},
            {"id": 2, "desc": "Aluguel", "valor": 1800, "tipo": "despesa", "cat": "Moradia", "mes": "2026-08"},
            {"id": 3, "desc": "Supermercado", "valor": 450, "tipo": "despesa", "cat": "Alimentação", "mes": "2026-08"},
            {"id": 4, "desc": "Uber", "valor": 120, "tipo": "despesa", "cat": "Transporte", "mes": "2026-08"},
            {"id": 5, "desc": "Cinema", "valor": 80, "tipo": "despesa", "cat": "Lazer", "mes": "2026-07"}
        ],
        "contas": [
            {"id": 1, "nome": "Nubank", "saldo": 3200},
            {"id": 2, "nome": "Itaú", "saldo": 1500}
        ],
        "faturas": [
            {"id": 1, "desc": "Cartão Nubank", "valor": 850.40, "vencimento": "2026-08-20", "status": "pendente"},
            {"id": 2, "desc": "Internet", "valor": 120.00, "vencimento": "2026-08-15", "status": "pendente"},
            {"id": 3, "desc": "Cartão C&A", "valor": 215.00, "vencimento": "2026-08-25", "status": "pendente"}
        ],
        "metas": [
            {"id": 1, "nome": "Reserva de Emergência", "alvo": 10000, "guardado": 4500},
            {"id": 2, "nome": "Novo iPhone", "alvo": 7000, "guardado": 1200}
        ],
        "projetos": [
            {"id": 1, "nome": "Viagem Itália 2027", "alvo": 15000, "guardado": 3000, "tipo": "viagem"},
            {"id": 2, "nome": "Reserva Financeira", "alvo": 5000, "guardado": 1500, "tipo": "reserva"}
        ]
    }

def carregar_dados():
    """Lê os dados de dados.json; cria o arquivo com o seed na 1ª execução."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            # Arquivo corrompido: recria a partir do seed (não quebra o app)
            seed = dados_iniciais()
            salvar_dados(seed)
            return seed
    seed = dados_iniciais()
    salvar_dados(seed)  # persiste imediatamente no disco
    return seed

def salvar_dados(dados):
    """Grava todos os dados em dados.json de forma atômica (evita corrupção)."""
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

# ---------- Rotas de página ----------
@app.route("/")
def home():
    if not session.get("logado"):
        return redirect(url_for("login"))
    return render_template("index.html", usuario=session.get("usuario"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()
        if usuario == USUARIO and senha == SENHA:
            session["logado"] = True
            session["usuario"] = usuario
            return redirect(url_for("home"))
        return render_template("login.html", erro="Usuário ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- API de dados ----------
@app.route("/api/dados", methods=["GET"])
def get_dados():
    """Retorna todos os dados do sistema."""
    return jsonify(carregar_dados())

@app.route("/api/dados", methods=["POST"])
def post_dados():
    """Salva todos os dados enviados pelo frontend."""
    try:
        dados = request.get_json()
        if not isinstance(dados, dict):
            return jsonify({"erro": "Payload inválido"}), 400
        salvar_dados(dados)
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"erro": "Falha ao salvar dados"}), 500

# ---------- Backup ----------
@app.route("/api/backup")
def backup():
    """Baixa uma cópia dos dados (o usuário escolhe onde salvar)."""
    if not os.path.exists(DATA_FILE):
        salvar_dados(carregar_dados())
    return send_file(
        DATA_FILE,
        as_attachment=True,
        download_name="backup_agenda.json",
        mimetype="application/json"
    )

# ---------- Tratamento de erros ----------
@app.errorhandler(404)
def nao_encontrado(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def erro_interno(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)