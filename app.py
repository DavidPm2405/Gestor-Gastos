from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Transaction
from datetime import datetime, date
import csv
import io
import calendar

app = Flask(__name__)
app.config["SECRET_KEY"] = "cambiar-en-produccion"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gastos.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Inicia sesión para continuar."

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
@login_required
def index():
    return redirect(url_for("dashboard"))


# ── Auth ────────────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("El usuario o email ya existe.", "danger")
        elif len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "warning")
        else:
            user = User(username=username, email=email,
                        password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Usuario o contraseña incorrectos.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    txs = Transaction.query.filter_by(user_id=current_user.id).all()

    # Totales globales
    total_income = sum(t.amount for t in txs if t.type == "income")
    total_expense = sum(t.amount for t in txs if t.type == "expense")
    balance = total_income - total_expense

    # Filtrar por mes/año seleccionado
    month_txs = [t for t in txs if t.date.year == year and t.date.month == month]
    month_income = sum(t.amount for t in month_txs if t.type == "income")
    month_expense = sum(t.amount for t in month_txs if t.type == "expense")

    # Datos para gráfico mensual (12 meses del año)
    monthly_income = []
    monthly_expense = []
    for m in range(1, 13):
        inc = sum(t.amount for t in txs if t.type == "income" and t.date.year == year and t.date.month == m)
        exp = sum(t.amount for t in txs if t.type == "expense" and t.date.year == year and t.date.month == m)
        monthly_income.append(inc)
        monthly_expense.append(exp)

    # Gastos por categoría (mes seleccionado)
    cat_data = {}
    for t in month_txs:
        if t.type == "expense":
            cat_data[t.category] = cat_data.get(t.category, 0) + t.amount

    recent = sorted(txs, key=lambda t: t.date, reverse=True)[:5]
    month_name = calendar.month_name[month]
    years = sorted({t.date.year for t in txs} | {today.year}, reverse=True)

    return render_template("dashboard.html",
        balance=balance, total_income=total_income, total_expense=total_expense,
        month_income=month_income, month_expense=month_expense,
        monthly_income=monthly_income, monthly_expense=monthly_expense,
        cat_labels=list(cat_data.keys()), cat_values=list(cat_data.values()),
        recent=recent, year=year, month=month, month_name=month_name,
        years=years, months=list(range(1, 13)), calendar=calendar)


# ── Transactions ─────────────────────────────────────────────────────────────

CATEGORIES = {
    "income":  ["Salario", "Freelance", "Inversiones", "Regalo", "Otro"],
    "expense": ["Alimentación", "Transporte", "Vivienda", "Salud",
                "Entretenimiento", "Ropa", "Educación", "Servicios", "Otro"],
}

@app.route("/transactions")
@login_required
def transactions():
    q = Transaction.query.filter_by(user_id=current_user.id)
    type_filter = request.args.get("type", "")
    cat_filter  = request.args.get("category", "")
    if type_filter:
        q = q.filter_by(type=type_filter)
    if cat_filter:
        q = q.filter_by(category=cat_filter)
    txs = q.order_by(Transaction.date.desc()).all()
    all_cats = CATEGORIES["income"] + CATEGORIES["expense"]
    return render_template("transactions.html", transactions=txs,
        type_filter=type_filter, cat_filter=cat_filter, all_cats=all_cats)


@app.route("/transactions/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("El monto debe ser un número positivo.", "warning")
            return redirect(url_for("add_transaction"))

        tx = Transaction(
            user_id=current_user.id,
            type=request.form["type"],
            category=request.form["category"],
            amount=amount,
            description=request.form.get("description", "").strip(),
            date=datetime.strptime(request.form["date"], "%Y-%m-%d").date(),
        )
        db.session.add(tx)
        db.session.commit()
        flash("Transacción agregada.", "success")
        return redirect(url_for("transactions"))

    return render_template("add_transaction.html",
        categories=CATEGORIES, today=date.today().isoformat())


@app.route("/transactions/delete/<int:tx_id>", methods=["POST"])
@login_required
def delete_transaction(tx_id):
    tx = db.get_or_404(Transaction, tx_id)
    if tx.user_id != current_user.id:
        flash("No autorizado.", "danger")
        return redirect(url_for("transactions"))
    db.session.delete(tx)
    db.session.commit()
    flash("Transacción eliminada.", "success")
    return redirect(url_for("transactions"))


# ── Export ───────────────────────────────────────────────────────────────────

@app.route("/export/csv")
@login_required
def export_csv():
    txs = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Fecha", "Tipo", "Categoría", "Descripción", "Monto"])
    for t in txs:
        tipo = "Ingreso" if t.type == "income" else "Gasto"
        writer.writerow([t.date, tipo, t.category, t.description, t.amount])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="gastos.csv")


@app.route("/export/excel")
@login_required
def export_excel():
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        flash("Instala openpyxl para exportar a Excel: pip install openpyxl", "warning")
        return redirect(url_for("transactions"))

    txs = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Transacciones"

    headers = ["Fecha", "Tipo", "Categoría", "Descripción", "Monto"]
    header_fill = PatternFill("solid", fgColor="4F81BD")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for row, t in enumerate(txs, 2):
        tipo = "Ingreso" if t.type == "income" else "Gasto"
        ws.append([str(t.date), tipo, t.category, t.description, t.amount])
        if t.type == "income":
            ws.cell(row=row, column=5).font = Font(color="217346")
        else:
            ws.cell(row=row, column=5).font = Font(color="C00000")

    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or "")) for c in col) + 4

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True, download_name="gastos.xlsx")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
