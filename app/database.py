import sqlite3
from app.config import DB_PATH

TOPICS_SEED = [
    ("M1", "M", "Eiwitsynthese",
     "DNA-structuur, RNA-typen (mRNA/tRNA/rRNA), transcriptie, translatie, aminozuren, codons, start-/stopcodons"),
    ("M2", "M", "Stofwisseling van de cel",
     "Celstructuur, passief transport (diffusie, osmose), actief transport, assimilatie, dissimilatie, enzymen, ATP"),
    ("M3", "M", "Zelforganisatie van cellen",
     "Genexpressie, celdifferentiatie, stamcellen, eiwittypen, emergente eigenschappen"),
    ("M4", "M", "Moleculaire en cellulaire interactie",
     "Genregulatie prokaryoten/eukaryoten, celsignalering, signaalmoleculen, actiepotentiaal, rustpotentiaal, neurotransmitters"),
    ("M7", "M", "Erfelijkheid",
     "Chromosomen, genen, allelen, monohybride/dihybride kruisingen, stamboomanalyse, biotechnologie, genetische modificatie"),
    ("M8", "M", "Selectie en mutaties",
     "Genmutaties (puntmutaties, frameshift), chromosoommutaties, genoomaberaties (polyploïdie, aneuploïdie), DNA-analyse, mutagene factoren"),
    ("O1", "O", "Stofwisseling van het organisme",
     "Vertering en opname, gaswisseling, uitscheiding, bloedsomloop, lymfestelsel, transport bij planten, metabole aandoeningen"),
    ("O2", "O", "Zelfregulatie van het organisme",
     "Homeostase, temperatuurregulatie, water-/zoutbalans, hormonale regulatie, endocriene klieren, zenuwstelsel, neuronen, terugkoppeling"),
    ("O3", "O", "Afweer van het organisme",
     "Aangeboren/verworven immuniteit, antilichamen, antigenen, B-cellen, T-cellen, MHC, complement, vaccinatie, actieve/passieve immuniteit"),
    ("O9", "O", "Reproductie van het organisme",
     "Seksuele/aseksuele voortplanting, gametogenese, bevruchting, zwangerschap, embryonale ontwikkeling, reproductieve hormonen, anticonceptie"),
    ("P1", "P", "Regulatie van ecosystemen",
     "Energiestroom, primaire productie, voedselketens, koolstofkringloop, stikstofkringloop, fosforcryclus, populatiedynamiek, draagkracht"),
    ("P3", "P", "Interactie in ecosystemen",
     "Voedselwebben, predator-prooi, parasitisme, mutualisme, symbiose, concurrentie, biodiversiteit, duurzame ontwikkeling, ecosysteemdiensten"),
    ("P4", "P", "Soortvorming en evolutie",
     "Natuurlijke selectie, genetische drift, genflow, Hardy-Weinberg principe, allelfrequentieberekeningen, reproductieve isolatie, soortvorming, fylogenie"),
    ("A5", "A", "Onderzoeksvaardigheden",
     "Onderzoeksvraag formuleren, hypothese opstellen, experiment opzetten, resultaten analyseren, conclusies trekken, grafieken interpreteren"),
    ("A1", "A", "Informatievaardigheden",
     "Informatie zoeken, beoordelen op betrouwbaarheid, selecteren en verwerken, bronnen gebruiken"),
]

_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    return _conn


def init_db():
    global _conn
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA foreign_keys = ON")

    cur = _conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS topics (
            id          TEXT PRIMARY KEY,
            level       TEXT NOT NULL,
            name        TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS exams (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            year        INTEGER NOT NULL,
            timeframe   INTEGER NOT NULL,
            max_score   INTEGER NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS questions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id         INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
            number          INTEGER NOT NULL,
            sub_number      TEXT,
            max_points      INTEGER NOT NULL,
            official_answer TEXT NOT NULL,
            topic_id        TEXT REFERENCES topics(id),
            question_text   TEXT
        );

        CREATE TABLE IF NOT EXISTS attempts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id     INTEGER NOT NULL REFERENCES exams(id),
            started_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            finished_at DATETIME,
            raw_score   INTEGER,
            grade       REAL
        );

        CREATE TABLE IF NOT EXISTS answers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id      INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
            question_id     INTEGER NOT NULL REFERENCES questions(id),
            student_answer  TEXT NOT NULL,
            earned_points   INTEGER,
            claude_feedback TEXT,
            graded_at       DATETIME,
            UNIQUE(attempt_id, question_id)
        );
    """)

    row = cur.execute("SELECT COUNT(*) FROM topics").fetchone()
    if row[0] == 0:
        cur.executemany(
            "INSERT INTO topics (id, level, name, description) VALUES (?, ?, ?, ?)",
            TOPICS_SEED,
        )

    _conn.commit()
