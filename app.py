from flask import Flask, render_template, request, redirect, url_for, flash, Response, abort
import io
import qrcode
from database import init_db, get_db, register_beekeeper, register_hive, register_batch, get_dashboard, get_batch, list_beekeepers, list_hives, list_batches, list_blocks
from blockchain import verify_chain

app = Flask(__name__)
app.secret_key = "change-this-development-secret"
init_db()

@app.route("/")
def index():
    return render_template("index.html", stats=get_dashboard(), batches=list_batches(limit=5), chain=verify_chain())

@app.route("/beekeepers", methods=["GET", "POST"])
def beekeepers():
    if request.method == "POST":
        try:
            register_beekeeper(request.form["name"], request.form.get("contact", ""), request.form.get("location", ""))
            flash("Beekeeper registered successfully.", "success")
            return redirect(url_for("beekeepers"))
        except ValueError as e:
            flash(str(e), "error")
    return render_template("beekeepers.html", beekeepers=list_beekeepers())

@app.route("/hives", methods=["GET", "POST"])
def hives():
    if request.method == "POST":
        try:
            register_hive(request.form["beekeeper_id"], request.form["location"], request.form.get("status", "Active"),
                          request.form.get("temperature") or None, request.form.get("humidity") or None,
                          request.form.get("inspection_date", ""))
            flash("Hive registered successfully.", "success")
            return redirect(url_for("hives"))
        except (ValueError, KeyError) as e:
            flash(str(e) or "Please check the form.", "error")
    return render_template("hives.html", hives=list_hives(), beekeepers=list_beekeepers())

@app.route("/batches", methods=["GET", "POST"])
def batches():
    if request.method == "POST":
        try:
            register_batch(
                request.form["batch_id"], request.form["hive_id"], request.form["harvest_date"],
                request.form["quantity"], request.form["unit"], request.form["flower_source"],
                request.form.get("location", ""), request.form.get("quality_status", "Not assessed"),
                request.form.get("notes", "")
            )
            flash("Honey batch saved and added to the hash chain.", "success")
            return redirect(url_for("batches"))
        except (ValueError, KeyError) as e:
            flash(str(e) or "Please check the form.", "error")
    return render_template("batches.html", batches=list_batches(), hives=list_hives())

@app.route("/trace", methods=["GET", "POST"])
def trace():
    batch = None
    verification = None
    if request.method == "POST" or request.args.get("batch_id"):
        batch_id = (request.form.get("batch_id") or request.args.get("batch_id") or "").strip()
        batch = get_batch(batch_id)
        if batch:
            verification = verify_chain(batch_id=batch_id)
        else:
            flash("No batch found with that Batch ID.", "error")
    return render_template("trace.html", batch=batch, verification=verification)

@app.route("/batch/<batch_id>/qr.png")
def batch_qr(batch_id):
    """Generate a QR code that opens this batch's traceability page."""
    batch = get_batch(batch_id)
    if not batch:
        abort(404)
    target_url = url_for("trace", batch_id=batch_id, _external=True)
    image = qrcode.make(target_url)
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return Response(output.getvalue(), mimetype="image/png",
                    headers={"Content-Disposition": f'inline; filename="{batch_id}-qr.png"'})

@app.route("/blockchain")
def blockchain():
    return render_template("blockchain.html", blocks=list_blocks(), verification=verify_chain())

@app.route("/health")
def health():
    return {"status": "ok", "app": "Honey Chain"}

if __name__ == "__main__":
    app.run(debug=True)
