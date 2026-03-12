#!/usr/bin/env python3
"""
Generate parent-friendly progress report CSV from Firestore JSON data.

- Names formatted as "Last, First" to match Infinite Campus
- No XP, portal, or gamification jargon — plain parent language
- Bilingual EN/ES comments
"""

import csv
from datetime import datetime
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EA_ROOT = os.path.dirname(SCRIPT_DIR)

# ── Name formatting ──────────────────────────────────────────────────────────

def to_ic_name(name: str) -> str:
    """Convert 'First Last1 Last2' → 'Last1 Last2, First' for Infinite Campus."""
    parts = name.strip().split()
    if len(parts) <= 1:
        return name
    first = parts[0]
    last = " ".join(parts[1:])
    return f"{last}, {first}"


# ── Comment generation (parent-friendly, no jargon) ─────────────────────────

BUCKET_TO_PARENT = {
    "THRIVING":     "consistently engaged",
    "ON_TRACK":     "meeting expectations",
    "COASTING":     "doing the minimum",
    "SPRINTING":    "making a strong recent push",
    "STRUGGLING":   "having difficulty keeping up",
    "DISENGAGING":  "losing engagement with the coursework",
    "INACTIVE":     "not participating",
    "COPYING":      "raising academic integrity concerns",
    "UNKNOWN":      "showing inconsistent participation",
}

BUCKET_TO_PARENT_ES = {
    "THRIVING":     "consistentemente comprometido/a",
    "ON_TRACK":     "cumpliendo con las expectativas",
    "COASTING":     "haciendo lo mínimo",
    "SPRINTING":    "mostrando un esfuerzo reciente fuerte",
    "STRUGGLING":   "teniendo dificultades para mantenerse al día",
    "DISENGAGING":  "perdiendo interés en el curso",
    "INACTIVE":     "sin participación",
    "COPYING":      "presentando preocupaciones de integridad académica",
    "UNKNOWN":      "mostrando participación inconsistente",
}


def _time_descriptor(minutes: float) -> tuple[str, str]:
    """Return (EN, ES) descriptors for time investment."""
    if minutes >= 200:
        return "significant time", "tiempo significativo"
    elif minutes >= 60:
        return "a reasonable amount of time", "una cantidad razonable de tiempo"
    elif minutes >= 20:
        return "some time", "algo de tiempo"
    elif minutes > 0:
        return "very little time", "muy poco tiempo"
    else:
        return "no recorded time", "sin tiempo registrado"


def _completion_descriptor(rate: float) -> tuple[str, str]:
    """Return (EN, ES) descriptors for completion rate."""
    if rate >= 90:
        return "nearly all", "casi todas"
    elif rate >= 70:
        return "most", "la mayoría de"
    elif rate >= 50:
        return "about half", "aproximadamente la mitad de"
    elif rate >= 25:
        return "some", "algunas"
    elif rate > 0:
        return "very few", "muy pocas"
    else:
        return "none", "ninguna de"


def generate_comment(name_first: str, cr: dict) -> tuple[str, str]:
    """Generate (EN, ES) parent-friendly comments from class report data."""
    bucket = cr.get("bucket", "UNKNOWN")
    comp = cr["completion_rate"]
    time_min = cr["total_time_minutes"]
    submitted = cr["assignments_submitted"]
    total = cr["assignments_total"]

    engage_en = BUCKET_TO_PARENT.get(bucket, "showing mixed participation")
    engage_es = BUCKET_TO_PARENT_ES.get(bucket, "mostrando participación mixta")
    time_en, time_es = _time_descriptor(time_min)
    comp_en, comp_es = _completion_descriptor(comp)

    # ── English ──
    en_parts = [f"{name_first} is {engage_en}."]

    if total > 0:
        en_parts.append(
            f"They have completed {comp_en} assigned tasks ({submitted} of {total})."
        )

    if time_min > 0:
        en_parts.append(
            f"They have invested {time_en} in their work ({int(time_min)} minutes total)."
        )
    else:
        en_parts.append("They have not logged meaningful time on assignments.")

    # Actionable nudge based on bucket
    if bucket in ("INACTIVE", "DISENGAGING"):
        en_parts.append(
            "I encourage you to check in with your student about completing "
            "their work and reaching out to me if there are any barriers."
        )
    elif bucket == "COASTING":
        en_parts.append(
            "With a bit more effort, they could make stronger progress. "
            "Encouraging them to spend more time on assignments would help."
        )
    elif bucket == "STRUGGLING":
        en_parts.append(
            "I am available for extra support — please don't hesitate to reach out."
        )
    elif bucket == "COPYING":
        en_parts.append(
            "I'd like to discuss their work habits — please reach out at your convenience."
        )
    elif bucket in ("THRIVING", "SPRINTING"):
        en_parts.append("Keep up the great work!")
    # ON_TRACK / UNKNOWN — no extra nudge

    en = " ".join(en_parts)

    # ── Spanish ──
    es_parts = [f"{name_first} está {engage_es}."]

    if total > 0:
        es_parts.append(
            f"Ha completado {comp_es} las tareas asignadas ({submitted} de {total})."
        )

    if time_min > 0:
        es_parts.append(
            f"Ha dedicado {time_es} a su trabajo ({int(time_min)} minutos en total)."
        )
    else:
        es_parts.append("No ha registrado tiempo significativo en las tareas.")

    if bucket in ("INACTIVE", "DISENGAGING"):
        es_parts.append(
            "Les animo a hablar con su estudiante sobre completar su trabajo "
            "y comunicarse conmigo si hay algún obstáculo."
        )
    elif bucket == "COASTING":
        es_parts.append(
            "Con un poco más de esfuerzo, podría lograr un progreso más sólido. "
            "Animarle a dedicar más tiempo a las tareas ayudaría."
        )
    elif bucket == "STRUGGLING":
        es_parts.append(
            "Estoy disponible para apoyo adicional — no dude en comunicarse."
        )
    elif bucket == "COPYING":
        es_parts.append(
            "Me gustaría hablar sobre sus hábitos de trabajo — por favor comuníquese cuando le convenga."
        )
    elif bucket in ("THRIVING", "SPRINTING"):
        es_parts.append("¡Sigan así con el excelente trabajo!")

    es = " ".join(es_parts)

    return en, es


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    input_path = os.path.join(EA_ROOT, "temp", f"progress-data-{today}.json")
    output_path = os.path.join(EA_ROOT, "temp", f"progress-report-{today}.csv")

    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for student in data["students"]:
        raw_name = student["name"]
        ic_name = to_ic_name(raw_name)
        first_name = raw_name.split()[0]

        for class_type, cr in student["classes"].items():
            en, es = generate_comment(first_name, cr)
            rows.append({
                "Student Name": ic_name,
                "Class": class_type,
                "Period": cr.get("period", "?"),
                "Completion": f"{cr['completion_rate']:.0f}%",
                "Time Invested": f"{int(cr['total_time_minutes'])} min",
                "Engagement": BUCKET_TO_PARENT.get(cr["bucket"], cr["bucket"]),
                "Comment (EN)": en,
                "Comment (ES)": es,
            })

    # Sort by class, then period, then name (to match IC order)
    rows.sort(key=lambda r: (r["Class"], r["Period"], r["Student Name"]))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Student Name", "Class", "Period", "Completion",
            "Time Invested", "Engagement", "Comment (EN)", "Comment (ES)",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")

    # Show a few sample rows
    print(f"\nSample rows:")
    for r in rows[:3]:
        print(f"  {r['Student Name']} | {r['Class']} P{r['Period']} | {r['Completion']} | {r['Engagement']}")
        print(f"    EN: {r['Comment (EN)'][:120]}...")
        print(f"    ES: {r['Comment (ES)'][:120]}...")
        print()


if __name__ == "__main__":
    main()
