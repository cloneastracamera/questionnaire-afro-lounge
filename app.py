from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, render_template_string, request


APP_DIR = Path(__file__).resolve().parent
DATABASE = APP_DIR / "reponses.db"


def init_database() -> None:
    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submitted_at TEXT NOT NULL,
                answers TEXT NOT NULL
            )
            """
        )



app = Flask(__name__)

init_database()

QUESTIONS = [
    {"id": "age", "label": "Quel âge avez-vous ?", "type": "radio", "options": ["Moins de 21 ans", "21–24 ans", "25–34 ans", "35–44 ans", "45–54 ans", "55 ans ou plus"]},
    {"id": "residence", "label": "Dans quelle ville ou quel département habitez-vous ?", "type": "text"},
    {"id": "frequency", "label": "À quelle fréquence sortez-vous dans un restaurant, un bar lounge ou un lieu dansant ?", "type": "radio", "options": ["Plusieurs fois par semaine", "Environ une fois par semaine", "Deux à trois fois par mois", "Environ une fois par mois", "Occasionnellement", "Jamais ou presque"]},
    {"id": "interest", "label": "Seriez-vous intéressé(e) par un bar lounge afro ?", "type": "radio", "options": ["1 — Pas du tout", "2", "3", "4", "5 — Très intéressé(e)"]},
    {"id": "transport", "label": "Quels moyens de transport utiliseriez-vous principalement ?", "type": "checkbox", "options": ["Métro", "Bus ou Noctilien", "Voiture personnelle", "Taxi ou VTC", "Vélo ou trottinette", "À pied"]},
    {"id": "metroDistance", "label": "Combien de minutes accepteriez-vous de marcher depuis une station de métro ?", "type": "radio", "options": ["Moins de 5 minutes", "Entre 5 et 10 minutes", "Entre 10 et 15 minutes", "Plus de 15 minutes si le lieu en vaut la peine"]},
    {"id": "parkingImportance", "label": "La proximité d’un parking ouvert la nuit est-elle importante pour vous ?", "type": "radio", "options": ["Indispensable", "Très importante", "Assez importante", "Peu importante", "Pas importante"]},
    {"id": "parkingDistance", "label": "Quelle distance maximale accepteriez-vous entre le parking et l’établissement ?", "type": "radio", "options": ["Moins de 200 mètres", "Entre 200 et 500 mètres", "Entre 500 mètres et 1 kilomètre", "Peu importe si le trajet est sécurisé"]},
    {"id": "locationCriteria", "label": "Quels éléments seraient les plus importants dans le choix de l’emplacement ?", "type": "checkbox", "max": 3, "options": ["Proximité du métro", "Parking accessible", "Quartier animé", "Sécurité en fin de soirée", "Accès rapide depuis Paris", "Facilité pour commander un VTC", "Absence de logements proches", "Cadre moderne et élégant", "Tarifs abordables"]},
    {"id": "time", "label": "À quel moment viendriez-vous le plus souvent ?", "type": "checkbox", "options": ["Afterwork, entre 17 h et 20 h", "Dîner, entre 20 h et 23 h", "Bar dansant, entre 23 h et 1 h 30", "Soirée de nuit, entre 1 h 30 et 6 h 30", "Brunch ou événement le dimanche", "Privatisation ou anniversaire"]},
    {"id": "days", "label": "Quels jours vous conviendraient le mieux ?", "type": "checkbox", "options": ["Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]},
    {"id": "activities", "label": "Quelles activités vous intéresseraient ?", "type": "checkbox", "options": ["Restaurant africain contemporain", "Tapas africaines à partager", "Afterwork", "Cocktails et mocktails", "DJ et bar dansant", "Concerts ou performances", "Soirées à thème", "Espace VIP", "Anniversaires", "Privatisations", "Brunch", "Retransmissions sportives"]},
    {"id": "music", "label": "Quelles ambiances musicales aimeriez-vous retrouver ?", "type": "checkbox", "options": ["Afrobeats", "Amapiano", "Rumba ou ndombolo", "Coupé-décalé", "Kompa ou zouk", "Dancehall", "R&B", "Hip-hop", "Afro-house", "Musiques généralistes et internationales"]},
    {"id": "budget", "label": "Quel budget moyen prévoiriez-vous par personne pour un repas et une boisson ?", "type": "radio", "options": ["Moins de 25 €", "Entre 25 et 39 €", "Entre 40 et 59 €", "Entre 60 et 79 €", "80 € ou plus"]},
    {"id": "entryPrice", "label": "Quel prix d’entrée accepteriez-vous pour une soirée avec DJ ?", "type": "radio", "options": ["Entrée gratuite", "Jusqu’à 10 €", "De 11 à 15 €", "De 16 à 20 €", "De 21 à 25 €", "Plus de 25 € avec une consommation incluse"]},
    {"id": "groupSize", "label": "Avec combien de personnes viendriez-vous généralement ?", "type": "radio", "options": ["Seul(e)", "À deux", "Groupe de 3 à 5 personnes", "Groupe de 6 à 10 personnes", "Groupe de plus de 10 personnes"]},
    {"id": "barriers", "label": "Qu’est-ce qui pourrait vous empêcher de venir ?", "type": "checkbox", "options": ["Difficulté de stationnement", "Éloignement du métro", "Insécurité à la sortie", "Prix trop élevés", "Musique trop forte", "Temps d’attente à l’entrée", "Sélection trop stricte à l’entrée", "Manque de places assises", "Offre alimentaire insuffisante", "Fermeture trop tôt"]},
    {"id": "priority", "label": "Quel serait votre critère numéro un pour choisir ce lieu ?", "type": "radio", "options": ["L’ambiance", "La musique", "La cuisine", "L’accessibilité", "La sécurité", "Le rapport qualité-prix"]},
]

SECTIONS = [
    {"title": "Votre profil", "subtitle": "Quelques repères pour mieux connaître nos futurs clients.", "ids": ["age", "residence", "frequency", "interest"]},
    {"title": "Le lieu idéal", "subtitle": "Aidez-nous à choisir un emplacement simple et rassurant.", "ids": ["transport", "metroDistance", "parkingImportance", "parkingDistance", "locationCriteria"]},
    {"title": "Votre soirée", "subtitle": "Rythme, activités et univers musical.", "ids": ["time", "days", "activities", "music"]},
    {"title": "Votre budget", "subtitle": "Les derniers détails pour construire une offre juste.", "ids": ["budget", "entryPrice", "groupSize", "barriers", "priority"]},
]


HTML = r"""
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Question Afro Lounge</title>
  <style>
    :root{--ink:#17130f;--cream:#f7f0e4;--gold:#d99635;--wine:#6b1935;--green:#153d33}
    *{box-sizing:border-box}html{background:var(--cream)}
    body{margin:0;color:var(--ink);font-family:Arial,Helvetica,sans-serif;background:radial-gradient(circle at 8% 8%,rgba(217,150,53,.16),transparent 26rem),radial-gradient(circle at 94% 28%,rgba(107,25,53,.1),transparent 28rem),var(--cream)}
    button,input{font:inherit}.shell{width:min(860px,100%);margin:auto;padding:36px 20px 56px;min-height:100vh}
    .hero{padding:22px 6px 34px}.brand{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
    .brand span{display:grid;place-items:center;width:42px;height:42px;border-radius:50%;color:#fff;background:var(--wine);font-family:Georgia,serif}
    .eyebrow{margin:48px 0 12px;color:var(--wine);font-size:12px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
    h1{margin:0;max-width:700px;font-family:Georgia,"Times New Roman",serif;font-size:clamp(42px,8vw,76px);line-height:.98;letter-spacing:-.045em}
    .intro{max-width:650px;margin:24px 0 42px;color:#5d544b;font-size:17px;line-height:1.7}
    .progress-meta{display:flex;justify-content:space-between;margin-bottom:9px;color:#6a5f55;font-size:12px;font-weight:700}
    .progress{height:7px;overflow:hidden;border-radius:9px;background:#e2d7c7}.progress span{display:block;height:100%;border-radius:9px;background:linear-gradient(90deg,var(--wine),var(--gold));transition:width .35s ease}
    .form-card{padding:clamp(24px,5vw,52px);border:1px solid rgba(88,65,42,.12);border-radius:28px;background:rgba(255,255,255,.82);box-shadow:0 24px 70px rgba(70,47,25,.1);backdrop-filter:blur(8px)}
    .section-title{display:flex;gap:18px;align-items:flex-start;padding-bottom:30px;border-bottom:1px solid #e7ded3}.section-title>p{margin:0;color:var(--gold);font-family:Georgia,serif;font-size:34px}
    .section-title h2{margin:0 0 7px;font:700 30px/1.1 Georgia,serif}.section-title span{color:#75695e;line-height:1.5}
    fieldset{margin:0;padding:32px 0;border:0;border-bottom:1px solid #eee5da;scroll-margin:20px}legend{width:100%;font-size:17px;font-weight:700;line-height:1.5}
    legend b{color:var(--wine);margin-right:6px}legend em{color:var(--wine);font-style:normal}.hint{margin:7px 0 0 27px;color:#8b7c6e;font-size:12px}
    .choices{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:18px}
    .choice{display:flex;align-items:center;gap:11px;min-height:52px;padding:12px 14px;text-align:left;color:#413931;border:1px solid #dfd4c7;border-radius:14px;background:#fff;cursor:pointer;transition:.18s ease}
    .choice:hover{border-color:#c9a169;transform:translateY(-1px)}.choice.selected{color:var(--wine);border-color:var(--wine);background:#fff7f4;box-shadow:inset 0 0 0 1px var(--wine)}
    .dot,.box{flex:0 0 21px;display:grid;place-items:center;width:21px;height:21px;color:#fff;border:1.5px solid #b6aa9e;font-size:12px}.dot{border-radius:50%}.box{border-radius:5px}.selected .dot,.selected .box{border-color:var(--wine);background:var(--wine)}
    input{width:100%;margin-top:18px;padding:16px;border:1px solid #d9cbbd;border-radius:13px;outline:0;background:#fff}input:focus{border-color:var(--wine);box-shadow:0 0 0 3px rgba(107,25,53,.12)}
    .error{margin:22px 0 0;padding:13px 15px;color:#7b1730;border-radius:12px;background:#fff0f2;font-size:14px}.actions{display:flex;justify-content:flex-end;gap:12px;padding-top:30px}
    .primary,.secondary{min-height:50px;padding:0 22px;border-radius:999px;font-weight:800;cursor:pointer}.primary{color:#fff;border:0;background:var(--green);box-shadow:0 8px 22px rgba(21,61,51,.18)}.primary span{margin-left:10px}.primary:disabled{opacity:.65}.secondary{color:#4f453c;border:1px solid #d8cbbb;background:transparent}
    footer{padding:28px 10px 0;color:#807266;text-align:center;font-size:12px}.success{margin:12vh auto 0;max-width:690px;padding:64px 35px;text-align:center;border-radius:30px;background:#fff;box-shadow:0 25px 80px rgba(70,47,25,.12)}
    .success-icon{display:grid;place-items:center;width:70px;height:70px;margin:auto;color:#fff;border-radius:50%;background:var(--green);font-size:30px}.success .eyebrow{margin:28px 0 13px}.success h1{font-size:clamp(42px,7vw,66px)}.success>p:last-child{color:#6f6359;line-height:1.7}
    [hidden]{display:none!important}@media(max-width:640px){.shell{padding:18px 12px 40px}.hero{padding:14px 6px 25px}.eyebrow{margin-top:38px}.intro{margin-bottom:28px;font-size:15px}.form-card{border-radius:20px}.section-title h2{font-size:25px}.choices{grid-template-columns:1fr}.actions{position:sticky;bottom:8px;padding:16px 0 0;background:linear-gradient(transparent,rgba(255,255,255,.96) 20%)}.primary{flex:1}}
  </style>
</head>
<body>
<main class="shell">
  <div id="questionnaire">
    <header class="hero">
      <div class="brand"><span>QA</span> Question Afro Lounge</div>
      <p class="eyebrow">Questionnaire anonyme · 3 minutes</p>
      <h1>Imaginons ensemble<br>votre futur lieu afro.</h1>
      <p class="intro">Restaurant, cocktails, musique et soirées : partagez vos habitudes pour nous aider à créer une expérience festive, élégante et accessible.</p>
      <div class="progress-meta"><span id="step-label">Étape 1 sur 4</span><span id="percent">25 %</span></div>
      <div class="progress"><span id="progress-bar" style="width:25%"></span></div>
    </header>
    <form id="survey" class="form-card">
      <div class="section-title"><p id="section-number">01</p><div><h2 id="section-title"></h2><span id="section-subtitle"></span></div></div>
      <div id="questions"></div>
      <p id="error" class="error" role="alert" hidden></p>
      <div class="actions"><button id="back" class="secondary" type="button" hidden>Retour</button><button id="next" class="primary" type="submit">Continuer <span>→</span></button></div>
    </form>
    <footer>Vos réponses sont anonymes et utilisées uniquement pour l’étude du projet.</footer>
  </div>
  <section id="success" class="success" hidden><span class="success-icon">✓</span><p class="eyebrow">Réponse enregistrée</p><h1>Merci pour votre avis.</h1><p>Votre réponse anonyme nous aide à imaginer un lieu afro lounge qui vous ressemble.</p></section>
</main>
<script>
const questions={{ questions|tojson }};
const sections={{ sections|tojson }};
const answers={};
let step=0;
const byId=id=>document.getElementById(id);
function escapeHtml(text){const div=document.createElement("div");div.textContent=text;return div.innerHTML}
function questionNumber(id){return questions.findIndex(q=>q.id===id)+1}
function render(){
  const section=sections[step], percent=(step+1)*25;
  byId("step-label").textContent=`Étape ${step+1} sur 4`;byId("percent").textContent=`${percent} %`;byId("progress-bar").style.width=`${percent}%`;
  byId("section-number").textContent=String(step+1).padStart(2,"0");byId("section-title").textContent=section.title;byId("section-subtitle").textContent=section.subtitle;
  byId("back").hidden=step===0;byId("next").innerHTML=step===3?'Envoyer ma réponse <span>→</span>':'Continuer <span>→</span>';
  byId("error").hidden=true;
  byId("questions").innerHTML=section.ids.map(id=>{
    const q=questions.find(x=>x.id===id), hint=q.max?`<p class="hint">${q.max} réponses maximum</p>`:"";
    if(q.type==="text") return `<fieldset id="${q.id}"><legend><b>${questionNumber(q.id)}.</b> ${escapeHtml(q.label)} <em>*</em></legend><input aria-label="${escapeHtml(q.label)}" data-id="${q.id}" value="${escapeHtml(answers[q.id]||"")}" placeholder="Votre réponse"></fieldset>`;
    const choices=q.options.map(option=>{const selected=q.type==="checkbox"?(answers[q.id]||[]).includes(option):answers[q.id]===option;return `<button type="button" class="choice ${selected?"selected":""}" data-id="${q.id}" data-value="${escapeHtml(option)}" aria-pressed="${selected}"><span class="${q.type==="checkbox"?"box":"dot"}">${selected?"✓":""}</span>${escapeHtml(option)}</button>`}).join("");
    return `<fieldset id="${q.id}"><legend><b>${questionNumber(q.id)}.</b> ${escapeHtml(q.label)} <em>*</em></legend>${hint}<div class="choices">${choices}</div></fieldset>`;
  }).join("");
  document.querySelectorAll(".choice").forEach(button=>button.addEventListener("click",()=>select(button.dataset.id,button.dataset.value)));
  document.querySelectorAll("input").forEach(input=>input.addEventListener("input",()=>{answers[input.dataset.id]=input.value}));
}
function select(id,value){
  const q=questions.find(x=>x.id===id);byId("error").hidden=true;
  if(q.type==="checkbox"){const current=answers[id]||[], exists=current.includes(value);if(!exists&&q.max&&current.length>=q.max){showError(`Choisissez ${q.max} réponses maximum pour cette question.`);return}answers[id]=exists?current.filter(x=>x!==value):[...current,value]}else answers[id]=value;
  render();
}
function showError(message){byId("error").textContent=message;byId("error").hidden=false}
function validate(){
  const missing=sections[step].ids.find(id=>!answers[id]||(Array.isArray(answers[id])&&answers[id].length===0)||(typeof answers[id]==="string"&&!answers[id].trim()));
  if(missing){showError("Merci de répondre à toutes les questions de cette étape.");byId(missing).scrollIntoView({behavior:"smooth",block:"center"});return false}return true;
}
byId("back").addEventListener("click",()=>{step--;render();window.scrollTo({top:0,behavior:"smooth"})});
byId("survey").addEventListener("submit",async event=>{
  event.preventDefault();if(!validate())return;
  if(step<3){step++;render();window.scrollTo({top:0,behavior:"smooth"});return}
  byId("next").disabled=true;byId("next").textContent="Envoi…";
  try{const response=await fetch("/api/responses",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({answers})});if(!response.ok)throw new Error();byId("questionnaire").hidden=true;byId("success").hidden=false;window.scrollTo({top:0,behavior:"smooth"})}
  catch(error){showError("Une erreur est survenue. Merci de réessayer.");byId("next").disabled=false;byId("next").innerHTML='Envoyer ma réponse <span>→</span>'}
});
render();
</script>
</body>
</html>
"""


@app.get("/")
def index() -> str:
    return render_template_string(HTML, questions=QUESTIONS, sections=SECTIONS)


@app.post("/api/responses")
def save_response():
    payload = request.get_json(silent=True) or {}
    answers = payload.get("answers")
    if not isinstance(answers, dict):
        return jsonify({"error": "Réponses invalides"}), 400

    missing = []
    for question in QUESTIONS:
        value = answers.get(question["id"])
        if value is None or value == "" or value == []:
            missing.append(question["id"])
        if question.get("max") and isinstance(value, list) and len(value) > question["max"]:
            return jsonify({"error": f"Trop de réponses pour {question['id']}"}), 400
    if missing:
        return jsonify({"error": "Questions sans réponse", "missing": missing}), 400

    submitted_at = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            "INSERT INTO responses (submitted_at, answers) VALUES (?, ?)",
            (submitted_at, json.dumps(answers, ensure_ascii=False)),
        )
    return jsonify({"saved": True}), 201


@app.get("/export.csv")
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    question_ids = [question["id"] for question in QUESTIONS]
    writer.writerow(["id", "date_envoi", *question_ids])

    with sqlite3.connect(DATABASE) as connection:
        rows = connection.execute(
            "SELECT id, submitted_at, answers FROM responses ORDER BY id DESC"
        ).fetchall()

    for response_id, submitted_at, raw_answers in rows:
        answers = json.loads(raw_answers)
        values = [
            " | ".join(answers.get(question_id, []))
            if isinstance(answers.get(question_id), list)
            else answers.get(question_id, "")
            for question_id in question_ids
        ]
        writer.writerow([response_id, submitted_at, *values])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=reponses_afro_lounge.csv"},
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
