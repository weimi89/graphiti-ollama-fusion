# Graphiti MCP Server

Υπηρεσία μνήμης γράφου γνώσης — διακομιστής MCP που ενσωματώνει πολλαπλούς παρόχους LLM (Ollama / GLM / GROQ / OpenRouter / DeepSeek) με τη βάση δεδομένων γράφου Neo4j.

Αναπτύχθηκε ως επέκταση του [getzep/graphiti](https://github.com/getzep/graphiti), υποστηρίζει ευέλικτη εναλλαγή μεταξύ τοπικού Ollama και cloud LLM, και επιτρέπει τον ανεξάρτητο ορισμό του παρόχου Embedding (αποσυνδεδεμένου από το LLM).

## Χαρακτηριστικά

- **Έξυπνη διαχείριση μνήμης** — Χρήση γράφου γνώσης για αποθήκευση και ανάκτηση σύνθετων σχέσεων μνήμης
- **Σημασιολογική αναζήτηση** — Υβριδική αναζήτηση βασισμένη σε διανυσματικά embeddings (διάνυσμα + λέξεις-κλειδιά + διάσχιση γράφου)
- **16 στρατηγικές αναζήτησης** — Η προηγμένη αναζήτηση υποστηρίζει πολλαπλούς τρόπους επανακατάταξης όπως RRF, MMR, Cross-Encoder
- **Πολλαπλοί πάροχοι LLM** — Υποστήριξη Ollama (τοπικό), GLM (Zhipu AI δωρεάν), GROQ (γρήγορη συμπερασματολογία), OpenRouter (συγκέντρωση μοντέλων από διάφορους παρόχους), DeepSeek, με εναλλαγή με ένα πάτημα μέσω μεταβλητών περιβάλλοντος
- **Αποσύνδεση Embedding και LLM** — Δυνατότητα ανεξάρτητου ορισμού του ενσωματωτή μέσω `EMBEDDING_PROVIDER`, με αυτόματη επιστροφή του cloud LLM στο τοπικό `bge-m3`
- **Διαχωρισμός διπλού μοντέλου** — Σε λειτουργία Ollama, οι σύνθετες εργασίες χρησιμοποιούν το κύριο μοντέλο, ενώ οι απλές εργασίες μεταβαίνουν αυτόματα σε μικρότερο μοντέλο για βελτίωση της απόδοσης
- **Έξυπνη κατάτμηση περιεχομένου** — Αυτόματη τμηματοποίηση μεγάλων κειμένων για μείωση του φόρτου του LLM (ρυθμιζόμενο όριο)
- **Επεξεργασία μνήμης στο παρασκήνιο** — Η προσθήκη μνήμης μπορεί να εκτελεστεί στο παρασκήνιο, με την κλήση MCP να επιστρέφει άμεσα
- **Αφαίρεση διπλότυπων μνήμης** — Αυτόματος εντοπισμός υψηλά παρόμοιων υπαρχουσών μνημών για αποφυγή διπλής αποθήκευσης
- **Εντοπισμός συγκρούσεων** — Ανίχνευση αντιφατικών γεγονότων μεταξύ δύο οντοτήτων, αναγνώριση ληγμένων και έγκυρων πληροφοριών
- **Εντοπισμός κοινοτήτων** — Αυτόματη ομαδοποίηση σχετικών οντοτήτων βάσει του αλγορίθμου Label Propagation
- **Παρακολούθηση σημαντικότητας** — Αυτόματη καταγραφή της συχνότητας πρόσβασης οντοτήτων, με τα αποτελέσματα αναζήτησης να κατατάσσονται βάσει σημαντικότητας
- **Έξυπνη λήθη** — Αναγνώριση και εκκαθάριση παρωχημένων μνημών με χαμηλή πρόσβαση, διατηρώντας τον γράφο συνοπτικό
- **Μαζική εισαγωγή** — Υποβολή πολλαπλών μνημών με μία φορά, κατάλληλη για μετεγκατάσταση μεγάλου όγκου δεδομένων
- **Δομημένες τριάδες** — Άμεση προσθήκη «υποκείμενο-σχέση-αντικείμενο», παρακάμπτοντας την εξαγωγή LLM, με ολοκλήρωση σε δευτερόλεπτα
- **Web διεπαφή διαχείρισης** — Ενσωματωμένος πίνακας ελέγχου, περιήγηση, αναζήτηση, οπτικοποίηση γράφου γνώσης, AI ερωταποκρίσεις, περιήγηση κοινοτήτων
- **Πολυγλωσσική υποστήριξη (i18n)** — Τα μηνύματα απόκρισης υποστηρίζουν 30+ locale (συμπεριλαμβανομένων zh-TW / en / zh-CN / ja / pt-BR / ko / es / de / fr κ.ά.)· τα εργαλεία MCP βασίζονται στο `SERVER_LANG`, ενώ το REST API διαπραγματεύεται αυτόματα βάσει του HTTP `Accept-Language`
- **Σκούρο/ανοιχτό θέμα** — Η Web διεπαφή υποστηρίζει εναλλαγή θέματος
- **Ασφαλής λειτουργία** — Δυνατότητα γρήγορης προσθήκης μνήμης που παρακάμπτει την εξαγωγή οντοτήτων
- **Υποστήριξη Docker** — Ενσωματωμένο Dockerfile, υποστήριξη ανάπτυξης σε container
- **Ασφάλεια ταυτόχρονης εκτέλεσης** — asyncio.Lock προστατεύει την αρχικοποίηση, αποτρέποντας συνθήκες ανταγωνισμού (race conditions)
- **Πολυεπίπεδος έλεγχος υγείας** — `/health` (liveness) + `/health/ready` (readiness)

## Απαιτήσεις συστήματος

| Στοιχείο | Απαίτηση |
|------|------|
| Python | 3.10+ (συνιστάται 3.11+) |
| Neo4j | 4.0+ (`bolt://localhost:7687`) |
| Πάροχος LLM | Ollama / GLM / GROQ / OpenRouter / DeepSeek (επιλογή ενός εκ των πέντε) |
| Node.js | 18+ (μόνο για εκτέλεση στο παρασκήνιο με PM2, προαιρετικό) |
| Χώρος δίσκου | ~3GB (μοντέλα Ollama + δεδομένα Neo4j) |

### Επιλογή παρόχου LLM

Εναλλαγή μέσω της μεταβλητής περιβάλλοντος `LLM_PROVIDER` (`ollama` / `glm` / `groq` / `openrouter` / `deepseek`):

| Πάροχος | Χαρακτηριστικά | Μοντέλο LLM | Embedding | Κατάλληλο σενάριο |
|--------|------|----------|-----------|----------|
| **Ollama** (προεπιλογή) | Πλήρως τοπικό, τα δεδομένα δεν φεύγουν από τη μηχανή | `qwen2.5:3b` | `bge-m3` (εξαιρετικό στα κινεζικά + RAG) | Με GPU, με έμφαση στην ιδιωτικότητα |
| **GLM** | Δωρεάν cloud, σταθερό χωρίς όρια ροής | `glm-4-flash` (δωρεάν) | `embedding-3` | Χωρίς GPU, σενάρια εντατικής αναζήτησης |
| **GROQ** | Εξαιρετικά γρήγορη συμπερασματολογία | `llama-3.3-70b-versatile` | επιστροφή σε Ollama `bge-m3` | Περιστασιακή εγγραφή, αναζήτηση ποιότητας |
| **OpenRouter** | Συγκέντρωση μοντέλων από διάφορους παρόχους, με δωρεάν όριο | `stepfun/step-3.5-flash:free` κ.ά. | επιστροφή σε Ollama `bge-m3` | Επιθυμία χρήσης συγκεκριμένου cloud μοντέλου |
| **DeepSeek** | Cloud της DeepSeek, υψηλή σχέση ποιότητας/τιμής | `deepseek-v4-flash` / `deepseek-v4-pro` | επιστροφή σε Ollama `bge-m3` | Κατανόηση κινεζικών, cloud χαμηλού κόστους |

> **Αποσύνδεση Embedding και LLM**: Ο ενσωματωτής ορίζεται ανεξάρτητα μέσω του `EMBEDDING_PROVIDER` (`ollama` / `glm`)· αν δεν οριστεί, ακολουθεί το `LLM_PROVIDER`. Στην πραγματικότητα μόνο το `glm` χρησιμοποιεί το GLM `embedding-3`, ενώ όλα τα υπόλοιπα (συμπεριλαμβανομένων των cloud LLM όπως GROQ / OpenRouter / DeepSeek που δεν παρέχουν Embedding) χρησιμοποιούν αυτόματα το Ollama `bge-m3`. **Επομένως, όταν χρησιμοποιείτε οποιοδήποτε cloud LLM, εξακολουθείτε να χρειάζεστε το τοπικό Ollama για την παροχή υπηρεσίας embedding (εκτός αν το embedding έχει επίσης οριστεί σε glm).**

#### Λειτουργία Ollama (τοπική)

```bash
# Κύριο μοντέλο LLM (συνιστάται qwen2.5:3b, βέλτιστη ισορροπία ταχύτητας και σταθερότητας)
ollama pull qwen2.5:3b

# Μοντέλο embedding (απαραίτητο, για διανυσματική αναζήτηση)
ollama pull bge-m3
```

> **Σημειώσεις επιλογής μοντέλου**:
> - `qwen2.5:3b` — Συνιστάται, ~2s/κλήση, ~100 t/s, 100% σταθερή δομημένη έξοδος στο graphiti-core
> - `qwen2.5:7b` — Καλύτερα αποτελέσματα αλλά 5-10 φορές πιο αργό, κατάλληλο για σενάρια που απαιτούν ποιότητα
> - `qwen2.5:1.5b` — Το ταχύτερο αλλά **ασταθές** (ποσοστό επιτυχίας δομημένου JSON μόνο 33%), δεν συνιστάται

#### Λειτουργία GLM (cloud Zhipu AI)

```bash
# Ρυθμίσεις .env
LLM_PROVIDER=glm
GLM_API_KEY=your_api_key          # Λήψη από https://open.bigmodel.cn
GLM_MODEL=glm-4-flash             # Δωρεάν μοντέλο
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768      # Πρέπει να ταιριάζει με τη διάσταση του διανυσματικού ευρετηρίου Neo4j
```

> **Αναφορά απόδοσης GLM**: Εγγραφή ~22s (σύντομο κείμενο), αναζήτηση ~0.34s, μηδέν σφάλματα Rate Limit, 2-5 φορές πιο αργό από το τοπικό Ollama αλλά εντελώς δωρεάν.

#### Λειτουργία GROQ (γρήγορη συμπερασματολογία)

```bash
# Ρυθμίσεις .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key         # Λήψη από https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Σημείωση**: Το GROQ δεν παρέχει υπηρεσία Embedding, απαιτείται συνδυασμός με τον ενσωματωτή Ollama (αυτόματη επιστροφή) ή ορισμός του `EMBEDDING_PROVIDER` σε glm. Το GROQ έχει αυστηρό Rate Limit, η υψηλής συχνότητας χρήση θα προκαλέσει πολλές επαναλήψεις.

#### Λειτουργία OpenRouter (συγκέντρωση μοντέλων από διάφορους παρόχους)

```bash
# Ρυθμίσεις .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key       # Λήψη από https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free   # Μπορεί να αλλάξει σε οποιοδήποτε μοντέλο OpenRouter
```

> **Σημείωση**: Το OpenRouter δεν παρέχει Embedding, επιστρέφει αυτόματα στο Ollama `bge-m3`. Η λίστα μοντέλων στο https://openrouter.ai/models (περιλαμβάνει πολλά δωρεάν μοντέλα `:free`).

#### Λειτουργία DeepSeek

```bash
# Ρυθμίσεις .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key         # Λήψη από https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash      # Συνιστάται· ή deepseek-v4-pro (καλύτερα αποτελέσματα)
```

> **Σημείωση**: Το DeepSeek δεν παρέχει Embedding, επιστρέφει αυτόματα στο Ollama `bge-m3`. Τα `deepseek-chat` / `deepseek-reasoner` θα αποσυρθούν στις 2026-07-24, συνιστάται η μετάβαση σε `deepseek-v4-flash` / `deepseek-v4-pro`. Το DeepSeek απαιτεί αυστηρά το prompt της λειτουργίας `json_object` να περιέχει τη συμβολοσειρά "json"· ο πελάτης διαθέτει ενσωματωμένη προστασία ασφαλείας, χωρίς ανάγκη επιπλέον ρύθμισης.

## Γρήγορη εκκίνηση

### 1. Προετοιμασία

Επιβεβαιώστε ότι το Neo4j εκτελείται τοπικά και προετοιμάστε την αντίστοιχη υπηρεσία βάσει του επιλεγμένου παρόχου LLM:

```bash
# Επιβεβαίωση ότι το Neo4j εκτελείται (απαραίτητο)
neo4j status
# Ή χρησιμοποιήστε Docker: docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

# Λειτουργία Ollama: επιβεβαίωση ότι το Ollama εκτελείται
ollama list
# Αν δεν έχει εκκινήσει: ollama serve

# Λειτουργία GLM / GROQ: απαιτείται μόνο έγκυρο API Key, χωρίς ανάγκη τοπικής υπηρεσίας
```

### 2. Εγκατάσταση εξαρτήσεων

```bash
git clone <repo-url>
cd graphiti
uv sync
```

> **Σημείωση**: Αυτό το έργο χρησιμοποιεί το [uv](https://github.com/astral-sh/uv) για τη διαχείριση εξαρτήσεων. Αν δεν είναι εγκατεστημένο: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Διαμόρφωση περιβάλλοντος

```bash
cp .env.example .env
```

Επεξεργαστείτε το `.env`, **τουλάχιστον** πρέπει να τροποποιήσετε τα παρακάτω στοιχεία:

```bash
NEO4J_PASSWORD=your_actual_password  # Απαραίτητο: κωδικός Neo4j
LLM_PROVIDER=ollama                  # ollama / glm / groq / openrouter / deepseek
OLLAMA_MODEL=qwen2.5:3b              # Λειτουργία Ollama: τοπικό μοντέλο LLM
# GLM_API_KEY=your_key               # Λειτουργία GLM: API Key του Zhipu AI
# GROQ_API_KEY=your_key              # Λειτουργία GROQ: GROQ API Key
# OPENROUTER_API_KEY=your_key        # Λειτουργία OpenRouter: API Key
# DEEPSEEK_API_KEY=your_key          # Λειτουργία DeepSeek: API Key
```

### 4. Εκκίνηση υπηρεσίας

```bash
# Λειτουργία HTTP (συνιστάται, περιλαμβάνει τη Web διεπαφή διαχείρισης)
uv run python graphiti_mcp_server.py --transport http --port 8000

# Ή χρήση PM2 για εκτέλεση στο παρασκήνιο (συνιστάται για μακροχρόνια λειτουργία)
pm2 start ecosystem.config.cjs
```

### 5. Επαλήθευση υπηρεσίας

Μετά την εκκίνηση μπορείτε να αποκτήσετε πρόσβαση στα παρακάτω endpoints:

| Endpoint | Περιγραφή |
|------|------|
| http://localhost:8000/ | Web διεπαφή διαχείρισης |
| http://localhost:8000/mcp | Endpoint MCP (για σύνδεση πελατών MCP) |
| http://localhost:8000/health | Έλεγχος υγείας (liveness) |
| http://localhost:8000/health/ready | Βαθύς έλεγχος (περιλαμβάνει σύνδεση Neo4j) |
| http://localhost:8000/api/stats | Στατιστικά REST API |

## Δομή έργου

```
graphiti/
├── graphiti_mcp_server.py        # Κύριο σημείο εισόδου — ορισμός εργαλείων MCP (19 εργαλεία)
├── src/
│   ├── config.py                 # Διαχείριση διαμόρφωσης (GraphitiConfig, υποστήριξη επιστρωμάτωσης JSON/.env)
│   ├── web_api.py                # REST API της Web διεπαφής διαχείρισης (20+ endpoints)
│   ├── ollama_graphiti_client.py  # Πελάτης LLM Ollama (διαχωρισμός διπλού μοντέλου)
│   ├── glm_client.py             # Πελάτης LLM GLM (Zhipu AI) (συμβατό OpenAI API)
│   ├── openrouter_client.py      # Πελάτης LLM OpenRouter (συγκέντρωση μοντέλων από διάφορους παρόχους)
│   ├── deepseek_client.py        # Πελάτης LLM DeepSeek (json_object + εφεδρική προστασία json)
│   ├── ollama_embedder.py        # Προσαρμογέας μοντέλου embedding Ollama
│   ├── content_preprocessor.py   # Έξυπνη κατάτμηση περιεχομένου (αυτόματη τμηματοποίηση μεγάλων κειμένων)
│   ├── deduplication.py          # Αφαίρεση διπλότυπων μνήμης (σύγκριση ομοιότητας συνημιτόνου)
│   ├── importance.py             # Παρακολούθηση σημαντικότητας και έξυπνη λήθη
│   ├── safe_memory_add.py        # Ασφαλής προσθήκη μνήμης (παράκαμψη εξαγωγής οντοτήτων)
│   ├── timezone_utils.py         # Μετατροπή ζώνης ώρας (εμφάνιση UTC→τοπική ζώνη ώρας)
│   ├── i18n.py                   # Πολυγλωσσική υποστήριξη backend (REST βάσει Accept-Language, MCP βάσει SERVER_LANG)
│   ├── exceptions.py             # Δομημένη διαχείριση εξαιρέσεων (12 κατηγορίες εξαιρέσεων)
│   └── logging_setup.py          # Σύστημα καταγραφής (χρονική περιστροφή + παρακολούθηση απόδοσης)
├── web/                          # Frontend Web διεπαφής διαχείρισης (SPA, χωρίς build)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Ενθυλάκωση REST API
│       ├── components.js         # Απόδοση στοιχείων UI (περιλαμβάνει σελίδα κοινοτήτων)
│       └── app.js                # Δρομολόγηση SPA, διαχείριση κατάστασης
├── tests/                        # Σουίτα δοκιμών (183 δοκιμές)
│   ├── test_content_preprocessor.py  # Δοκιμές λογικής κατάτμησης (17)
│   ├── test_new_features.py      # Δοκιμές νέων λειτουργιών (32)
│   ├── test_i18n.py             # Δοκιμές πολυγλωσσικής υποστήριξης (37)
│   ├── test_unit.py              # Δοκιμές μονάδας
│   ├── test_web_api.py           # Δοκιμές Web API
│   ├── test_web_ui_features.py   # Δοκιμές λειτουργιών Web UI
│   ├── test_integration_manual.py # Χειροκίνητες δοκιμές ολοκλήρωσης
│   └── bench_deepseek_flash_vs_pro.py # Σενάριο benchmark απόδοσης DeepSeek flash/pro
├── tools/                        # Εργαλεία ανάπτυξης και διάγνωσης
│   ├── status_report.py          # Ενοποιημένη αναφορά κατάστασης
│   ├── validate_config.py        # Επαλήθευση διαμόρφωσης
│   ├── performance_diagnose.py   # Διάγνωση απόδοσης
│   ├── inspect_schema.py         # Έλεγχος δομής Neo4j
│   └── batch_reprocess.py        # Μαζική επανεπεξεργασία
├── docs/                         # Τεκμηρίωση
├── logs/                         # Καταγραφές (χρονική περιστροφή, προεπιλεγμένη διατήρηση 30 ημερών)
├── Dockerfile                    # Ανάπτυξη container Docker
└── ecosystem.config.cjs          # Διαμόρφωση PM2
```

## Ρύθμιση πελάτη MCP

### Λειτουργία HTTP (συνιστάται)

Κατάλληλη για πελάτες MCP που υποστηρίζουν HTTP όπως Claude Code, Cline:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Λειτουργία STDIO

Κατάλληλη για πελάτες που χρειάζονται άμεση εκκίνηση διεργασίας όπως το Claude Desktop:

**Τοποθεσία αρχείου διαμόρφωσης:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/graphiti",
        "python", "graphiti_mcp_server.py", "--transport", "stdio"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password"
      }
    }
  }
}
```

> **Σημείωση**: Η λειτουργία SSE (`--transport sse`) δεν συνιστάται πλέον. Το MCP 1.x έχει προβλήματα συμβατότητας αρχικοποίησης session, χρησιμοποιήστε τη λειτουργία HTTP.

## Εργαλεία MCP (19)

### Διαχείριση μνήμης (7)

| Εργαλείο | Περιγραφή |
|------|------|
| `add_memory_simple` | Προσθήκη μνήμης στον γράφο γνώσης (υποστήριξη επεξεργασίας στο παρασκήνιο, έξυπνης κατάτμησης, ελέγχου διπλότυπων) |
| `add_episode_bulk` | Μαζική προσθήκη πολλαπλών μνημών (προεπιλογή επεξεργασία στο παρασκήνιο) |
| `add_triplet` | Προσθήκη δομημένης τριάδας (παράκαμψη LLM, ολοκλήρωση σε δευτερόλεπτα) |
| `search_memory_nodes` | Αναζήτηση κόμβων μνήμης (υποστήριξη 16 στρατηγικών αναζήτησης, χρονικό φιλτράρισμα) |
| `search_memory_facts` | Αναζήτηση γεγονότων μνήμης (υποστήριξη φιλτραρίσματος τύπου σχέσης, χρονικού εύρους, φιλτραρίσματος εγκυρότητας) |
| `advanced_search` | Προηγμένη αναζήτηση (16 στρατηγικές, επιστροφή κόμβων+ακμών+κοινοτήτων+επεισοδίων) |
| `get_episodes` | Λήψη πρόσφατων επεισοδίων μνήμης |

### Ανάλυση γνώσης (3)

| Εργαλείο | Περιγραφή |
|------|------|
| `check_conflicts` | Εντοπισμός συγκρούσεων γεγονότων μεταξύ δύο οντοτήτων (έγκυρα vs ληγμένα) |
| `get_node_edges` | Εξερεύνηση εισερχόμενων και εξερχόμενων σχέσεων ακμών κόμβου |
| `build_communities` | Ενεργοποίηση εντοπισμού και ομαδοποίησης κοινοτήτων (προεπιλογή επεξεργασία στο παρασκήνιο) |

### Συντήρηση μνήμης (2)

| Εργαλείο | Περιγραφή |
|------|------|
| `get_stale_memories` | Αναζήτηση παρωχημένων μνημών με χαμηλή πρόσβαση |
| `cleanup_stale_memories` | Εκκαθάριση παρωχημένων μνημών (προεπιλογή λειτουργία προεπισκόπησης dry_run) |

### Διαχείριση εργασιών

| Εργαλείο | Περιγραφή |
|------|------|
| `get_memory_task_status` | Αναζήτηση προόδου και αποτελεσμάτων εργασίας επεξεργασίας μνήμης στο παρασκήνιο |

### Διαγραφή και αναζήτηση

| Εργαλείο | Περιγραφή |
|------|------|
| `delete_episode` | Διαγραφή επεισοδίου μνήμης |
| `delete_entity_edge` | Διαγραφή ακμής οντότητας (σχέση) |
| `get_entity_edge` | Λήψη λεπτομερών πληροφοριών ακμής οντότητας |

### Διαχείριση συστήματος

| Εργαλείο | Περιγραφή |
|------|------|
| `get_status` | Λήψη κατάστασης υπηρεσίας (Neo4j, LLM, ενσωματωτής) |
| `test_connection` | Δοκιμή σύνδεσης Neo4j / LLM / ενσωματωτή |
| `clear_graph` | Εκκαθάριση βάσης δεδομένων γράφου (υποστήριξη εκκαθάρισης ανά group_id) |

## Παράμετροι εργαλείων

### add_memory_simple

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `name` | string | Y | | Όνομα μνήμης |
| `episode_body` | string | Y | | Περιεχόμενο μνήμης (αυτόματη κατάτμηση πάνω από 800 χαρακτήρες) |
| `group_id` | string | | `"default"` | ID ομάδας (συνιστάται απομόνωση ανά έργο) |
| `source` | string | | `"text"` | Τύπος πηγής: `text` / `json` / `message` |
| `source_description` | string | | `"MCP Server"` | Περιγραφή πηγής |
| `use_safe_mode` | bool | | `false` | Ασφαλής λειτουργία (παράκαμψη εξαγωγής οντοτήτων, γρήγορη αλλά η μνήμη δεν είναι αναζητήσιμη) |
| `background` | bool | | `false` | Επεξεργασία στο παρασκήνιο (άμεση επιστροφή task_id, κατάλληλο για μεγάλα κείμενα) |
| `force` | bool | | `false` | Παράκαμψη ελέγχου διπλότυπων (αναγκαστική προσθήκη) |
| `excluded_entity_types` | list | | | Εξαιρούμενοι τύποι οντοτήτων (μείωση ανεπιθύμητης εξαγωγής) |

> **Συμβουλές απόδοσης**:
> - Σύντομα κείμενα (<800 χαρακτήρες): άμεση επεξεργασία, συνήθως ολοκλήρωση σε 30-40 δευτερόλεπτα
> - Μεγάλα κείμενα (>800 χαρακτήρες): αυτόματη κατάτμηση σε πολλαπλά τμήματα, χρήση `add_episode_bulk` για ταυτόχρονη επεξεργασία (~33% πιο γρήγορη από τη σειριακή)
> - Η χρήση `background=true` αποφεύγει το μπλοκάρισμα της κλήσης MCP, παρακολούθηση προόδου μέσω `get_memory_task_status`
> - Το `use_safe_mode=true` ολοκληρώνεται σε δευτερόλεπτα αλλά η μνήμη δεν μπορεί να βρεθεί από τα εργαλεία search
> - Όταν είναι ενεργοποιημένη η αφαίρεση διπλότυπων, οι υψηλά παρόμοιες μνήμες προειδοποιούνται (το `force=true` παρακάμπτει)

### add_episode_bulk

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `episodes` | list | Y | | Λίστα μνημών, κάθε στοιχείο περιέχει `name` και `content` |
| `group_id` | string | | `"default"` | ID ομάδας |
| `source` | string | | `"text"` | Τύπος πηγής |
| `background` | bool | | `true` | Επεξεργασία στο παρασκήνιο (η μαζική επεξεργασία είναι συνήθως χρονοβόρα) |

### add_triplet

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `source_name` | string | Y | | Όνομα πηγαίας οντότητας (π.χ. "Alice") |
| `target_name` | string | Y | | Όνομα οντότητας στόχου (π.χ. "Google") |
| `relation_name` | string | Y | | Όνομα σχέσης (π.χ. "works_at") |
| `fact` | string | Y | | Περιγραφή γεγονότος (π.χ. "Alice works at Google") |
| `group_id` | string | | `"default"` | ID ομάδας |
| `source_labels` | list | | | Ετικέτες πηγαίας οντότητας |
| `target_labels` | list | | | Ετικέτες οντότητας στόχου |

### search_memory_nodes

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `query` | string | Y | | Λέξεις-κλειδιά αναζήτησης (φυσική γλώσσα) |
| `max_nodes` | int | | `10` | Μέγιστος αριθμός επιστροφής |
| `group_ids` | list | | | Φιλτράρισμα ομάδας (κοινή αναζήτηση πολλαπλών ομάδων) |
| `entity_types` | list | | | Φιλτράρισμα τύπου οντότητας |
| `search_recipe` | string | | | Στρατηγική αναζήτησης (βλ. προηγμένη αναζήτηση) |
| `created_after` | string | | | Κάτω όριο χρόνου δημιουργίας (ISO datetime) |
| `created_before` | string | | | Άνω όριο χρόνου δημιουργίας (ISO datetime) |

### search_memory_facts

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `query` | string | Y | | Λέξεις-κλειδιά αναζήτησης |
| `max_facts` | int | | `10` | Μέγιστος αριθμός επιστροφής |
| `group_ids` | list | | | Φιλτράρισμα ομάδας |
| `center_node_uuid` | string | | | UUID κεντρικού κόμβου (εξερεύνηση σχέσεων συγκεκριμένου κόμβου) |
| `edge_types` | list | | | Φιλτράρισμα τύπου σχέσης (π.χ. `["works_at"]`) |
| `created_after` | string | | | Κάτω όριο χρόνου δημιουργίας (ISO datetime) |
| `created_before` | string | | | Άνω όριο χρόνου δημιουργίας (ISO datetime) |
| `only_valid` | bool | | `false` | Επιστροφή μόνο μη ληγμένων γεγονότων |

### advanced_search

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `query` | string | Y | | Λέξεις-κλειδιά αναζήτησης |
| `search_recipe` | string | | `"combined_rrf"` | Στρατηγική αναζήτησης (16 επιλογές) |
| `max_results` | int | | `10` | Μέγιστος αριθμός επιστροφής |
| `group_ids` | list | | | Φιλτράρισμα ομάδας |
| `center_node_uuid` | string | | | UUID κεντρικού κόμβου |

**Διαθέσιμες στρατηγικές αναζήτησης (search_recipe):**

| Κατηγορία | Στρατηγική | Περιγραφή |
|------|------|------|
| Συνδυασμένη | `combined_rrf` | Συνδυασμένη σύντηξη RRF (προεπιλογή, συνιστάται) |
| Συνδυασμένη | `combined_mmr` | Συνδυασμένη επανακατάταξη ποικιλομορφίας MMR |
| Συνδυασμένη | `combined_cross_encoder` | Συνδυασμένη ακριβής κατάταξη Cross-Encoder |
| Ακμή | `edge_rrf` / `edge_mmr` / `edge_cross_encoder` | Αναζήτηση ακμών (3 τρόποι κατάταξης) |
| Ακμή | `edge_node_distance` / `edge_episode_mentions` | Αναζήτηση ακμών (απόσταση γράφου/αριθμός αναφορών) |
| Κόμβος | `node_rrf` / `node_mmr` / `node_cross_encoder` | Αναζήτηση κόμβων (3 τρόποι κατάταξης) |
| Κόμβος | `node_node_distance` / `node_episode_mentions` | Αναζήτηση κόμβων (απόσταση γράφου/αριθμός αναφορών) |
| Κοινότητα | `community_rrf` / `community_mmr` / `community_cross_encoder` | Αναζήτηση κοινοτήτων |

### check_conflicts

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `source_name` | string | Y | | Όνομα πηγαίας οντότητας |
| `target_name` | string | Y | | Όνομα οντότητας στόχου |
| `group_id` | string | | `"default"` | ID ομάδας |

### get_node_edges

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `node_uuid` | string | Y | | UUID κόμβου |
| `include_inbound` | bool | | `true` | Συμπερίληψη εισερχόμενων ακμών |
| `include_outbound` | bool | | `true` | Συμπερίληψη εξερχόμενων ακμών |
| `max_edges` | int | | `50` | Μέγιστος αριθμός επιστροφής |

### build_communities

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `group_ids` | list | | | Καθορισμένη ομάδα (αν κενό τότε όλες) |
| `background` | bool | | `true` | Επεξεργασία στο παρασκήνιο |

### get_stale_memories

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Πέρα από πόσες ημέρες χωρίς πρόσβαση θεωρείται παρωχημένο |
| `min_access_count` | int | | `2` | Συμπερίληψη μόνο αν ο αριθμός προσβάσεων είναι κάτω από αυτή την τιμή |
| `group_id` | string | | | Φιλτράρισμα ομάδας |
| `limit` | int | | `50` | Μέγιστος αριθμός επιστροφής |

### cleanup_stale_memories

| Παράμετρος | Τύπος | Απαραίτητο | Προεπιλογή | Περιγραφή |
|------|------|------|--------|------|
| `days_threshold` | int | | `30` | Όριο ημερών παρωχημένου |
| `min_access_count` | int | | `2` | Όριο ελάχιστου αριθμού προσβάσεων |
| `group_id` | string | | | Φιλτράρισμα ομάδας |
| `dry_run` | bool | | `true` | Λειτουργία προεπισκόπησης (χωρίς πραγματική διαγραφή) |
| `limit` | int | | `50` | Μέγιστος αριθμός επεξεργασίας |

### get_memory_task_status

| Παράμετρος | Τύπος | Απαραίτητο | Περιγραφή |
|------|------|------|------|
| `task_id` | string | Y | ID εργασίας παρασκηνίου (επιστρέφεται από `add_memory_simple(background=true)`) |

## Web διεπαφή διαχείρισης

Σε λειτουργία HTTP, επισκεφθείτε το `http://localhost:8000/` για χρήση.

**Λειτουργίες:**
- Πίνακας ελέγχου — Στατιστικά αριθμού κόμβων, γεγονότων, επεισοδίων μνήμης
- Κόμβοι οντοτήτων — Περιήγηση, φιλτράρισμα, διανυσματική αναζήτηση
- Σχέσεις γεγονότων — Περιήγηση, φιλτράρισμα, διανυσματική αναζήτηση
- Επεισόδια μνήμης — Περιήγηση, αναζήτηση πλήρους κειμένου, διαγραφή
- Περιήγηση κοινοτήτων — Λίστα κόμβων κοινοτήτων, περιλήψεις, ενεργοποίηση κατασκευής κοινοτήτων
- Φόρμα τριάδων — Άμεση προσθήκη δομημένης γνώσης «υποκείμενο-σχέση-αντικείμενο»
- Διαχείριση Group — Φιλτράρισμα ανά ομάδα, μαζική διαγραφή
- Οπτικοποίηση γράφου γνώσης — Γραφική αναπαράσταση σχέσεων κόμβων
- AI ερωταποκρίσεις — Έξυπνες ερωταποκρίσεις βάσει γράφου γνώσης
- Ανάλυση ποιότητας — Ανάλυση ποιότητας και κάλυψης μνήμης
- Εναλλαγή θέματος — Σκούρο/ανοιχτό θέμα

**REST API:**

| Endpoint | Μέθοδος | Περιγραφή |
|------|------|------|
| `/api/stats` | GET | Στατιστικά πίνακα ελέγχου |
| `/api/groups` | GET | Λήψη όλων των group_id |
| `/api/nodes` | GET | Περιήγηση κόμβων οντοτήτων (σελιδοποίηση) |
| `/api/facts` | GET | Περιήγηση γεγονότων (σελιδοποίηση) |
| `/api/episodes` | GET | Περιήγηση επεισοδίων μνήμης (σελιδοποίηση) |
| `/api/search/nodes` | GET | Διανυσματική αναζήτηση κόμβων |
| `/api/search/facts` | GET | Διανυσματική αναζήτηση γεγονότων |
| `/api/search/advanced` | GET | Προηγμένη αναζήτηση (16 στρατηγικές) |
| `/api/communities` | GET | Περιήγηση κόμβων κοινοτήτων (σελιδοποίηση) |
| `/api/communities/build` | POST | Ενεργοποίηση κατασκευής κοινοτήτων |
| `/api/memory/add-bulk` | POST | Μαζική προσθήκη μνήμης |
| `/api/memory/add-triplet` | POST | Προσθήκη τριάδας |
| `/api/memory/tasks` | GET | Λίστα εργασιών παρασκηνίου (υποστήριξη φιλτραρίσματος κατάστασης) |
| `/api/memory/tasks/{id}` | GET | Αναζήτηση κατάστασης μεμονωμένης εργασίας |
| `/api/analytics/stale` | GET | Αναζήτηση παρωχημένων μνημών |
| `/api/analytics/cleanup` | POST | Εκκαθάριση παρωχημένων μνημών |
| `/api/nodes/{uuid}` | DELETE | Διαγραφή κόμβου |
| `/api/episodes/{uuid}` | DELETE | Διαγραφή επεισοδίου μνήμης |
| `/api/facts/{uuid}` | DELETE | Διαγραφή γεγονότος |
| `/api/groups/{group_id}` | DELETE | Διαγραφή ολόκληρου του group |

## Διαμόρφωση

### Μεταβλητές περιβάλλοντος (.env)

Η διαμόρφωση χρησιμοποιεί μηχανισμό επιστρωμάτωσης: το αρχείο διαμόρφωσης JSON ως βάση, με τις μεταβλητές περιβάλλοντος να υπερισχύουν μεμονωμένων τιμών.

```bash
# === Απαραίτητα ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password        # Πρέπει να τροποποιηθεί

# === Επιλογή παρόχου LLM ===
LLM_PROVIDER=ollama                 # ollama / glm / groq / openrouter / deepseek

# === Πάροχος Embedding (προαιρετικό, προεπιλογή ακολουθεί το LLM_PROVIDER) ===
# Μόνο το glm χρησιμοποιεί GLM Embedding, όλα τα υπόλοιπα χρησιμοποιούν Ollama bge-m3
# EMBEDDING_PROVIDER=ollama         # ollama / glm

# === Διαμόρφωση Ollama (χρησιμοποιείται όταν LLM_PROVIDER=ollama) ===
OLLAMA_MODEL=qwen2.5:3b             # Κύριο μοντέλο (συνιστάται qwen2.5:3b)
OLLAMA_SMALL_MODEL=qwen2.5:3b       # Μικρό μοντέλο (για απλές εργασίες, μπορεί να είναι διαφορετικό μοντέλο)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# === Διαμόρφωση GLM (χρησιμοποιείται όταν LLM_PROVIDER=glm) ===
GLM_API_KEY=your_api_key            # Λήψη από https://open.bigmodel.cn
GLM_MODEL=glm-4-flash               # Δωρεάν μοντέλο
GLM_EMBEDDING_MODEL=embedding-3
GLM_EMBEDDING_DIMENSIONS=768

# === Διαμόρφωση GROQ (χρησιμοποιείται όταν LLM_PROVIDER=groq) ===
GROQ_API_KEY=your_api_key           # Λήψη από https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# === Διαμόρφωση OpenRouter (χρησιμοποιείται όταν LLM_PROVIDER=openrouter) ===
OPENROUTER_API_KEY=your_api_key     # Λήψη από https://openrouter.ai/keys
OPENROUTER_MODEL=stepfun/step-3.5-flash:free

# === Διαμόρφωση DeepSeek (χρησιμοποιείται όταν LLM_PROVIDER=deepseek) ===
DEEPSEEK_API_KEY=your_api_key       # Λήψη από https://platform.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash    # Ή deepseek-v4-pro

# === Μοντέλο embedding Ollama (χρησιμοποιείται σε όλες τις περιπτώσεις εκτός embedding glm) ===
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_EMBEDDING_DIMENSIONS=768

# === Εμφάνιση και γλώσσα (προαιρετικό) ===
GRAPHITI_DISPLAY_TIMEZONE=Asia/Taipei # Ζώνη ώρας εμφάνισης των χρονοσφραγίδων που επιστρέφει το API (όνομα IANA· η αποθήκευση παραμένει UTC)
SERVER_LANG=zh-TW                     # Γλώσσα απόκρισης εργαλείων MCP (πλήρη locale βλ. src/i18n.py)· το REST API βασίζεται στο Accept-Language

# === Απόδοση μνήμης (προαιρετικό) ===
GRAPHITI_CHUNK_THRESHOLD=800         # Όριο αριθμού χαρακτήρων για ενεργοποίηση έξυπνης κατάτμησης
GRAPHITI_MAX_CHUNK_SIZE=600          # Μέγιστος αριθμός χαρακτήρων ανά τμήμα
GRAPHITI_MAX_COROUTINES=10            # Μέγιστος αριθμός ταυτόχρονων coroutines
GRAPHITI_DEFAULT_BACKGROUND=false    # Αν είναι προεπιλογή η επεξεργασία στο παρασκήνιο

# === Παρακολούθηση σημαντικότητας και έξυπνη λήθη (προαιρετικό) ===
ENABLE_IMPORTANCE_TRACKING=true      # Ενεργοποίηση παρακολούθησης πρόσβασης
IMPORTANCE_WEIGHT=0.1                # Βάρος σημαντικότητας
STALE_DAYS_THRESHOLD=30              # Όριο ημερών παρωχημένου
STALE_MIN_ACCESS_COUNT=2             # Ελάχιστος αριθμός προσβάσεων

# === Καταγραφή ===
LOG_FILE=logs/graphiti_mcp_server.log
LOG_LEVEL=INFO
```

> **Για την πλήρη λίστα μεταβλητών περιβάλλοντος** ανατρέξτε στο `.env.example`

### Αρχείο διαμόρφωσης JSON

Κατάλληλο για διαμόρφωση που απαιτεί έλεγχο εκδόσεων (οι μεταβλητές περιβάλλοντος εξακολουθούν να μπορούν να υπερισχύσουν):

```bash
uv run python graphiti_mcp_server.py --config config.json --transport http
```

```json
{
  "llm_provider": "ollama",
  "embedding_provider": "",
  "ollama": {
    "model": "qwen2.5:3b",
    "small_model": "qwen2.5:3b",
    "base_url": "http://localhost:11434"
  },
  "glm": {
    "api_key": "your_api_key",
    "model": "glm-4-flash",
    "embedding_model": "embedding-3",
    "embedding_dimensions": 768
  },
  "groq": {
    "api_key": "your_api_key",
    "model": "llama-3.3-70b-versatile"
  },
  "openrouter": {
    "api_key": "your_api_key",
    "model": "stepfun/step-3.5-flash:free"
  },
  "deepseek": {
    "api_key": "your_api_key",
    "model": "deepseek-v4-flash"
  },
  "embedder": {
    "model": "bge-m3",
    "dimensions": 768
  },
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your_password"
  },
  "memory_performance": {
    "chunk_threshold": 800,
    "max_chunk_size": 600,
    "max_coroutines": 10,
    "default_background": false
  }
}
```

## Εκτέλεση στο παρασκήνιο με PM2

```bash
npm install -g pm2

pm2 start ecosystem.config.cjs      # Εκκίνηση
pm2 status                           # Κατάσταση
pm2 logs graphiti-mcp-http           # Καταγραφές σε πραγματικό χρόνο
pm2 restart graphiti-mcp-http --update-env  # Επανεκκίνηση (επαναφόρτωση .env)

pm2 save && pm2 startup              # Ρύθμιση αυτόματης εκκίνησης κατά την εκκίνηση συστήματος
```

> **Συμβουλή**: Μετά την τροποποίηση του `.env` πρέπει να γίνει επανεκκίνηση με τη σημαία `--update-env`, διαφορετικά οι μεταβλητές περιβάλλοντος δεν θα ενημερωθούν.

## Ανάπτυξη Docker

```bash
docker build -t graphiti-mcp .

# Σημείωση: Το container Docker πρέπει να μπορεί να συνδεθεί με Neo4j και Ollama
# Η χρήση host network είναι ο απλούστερος τρόπος
docker run -p 8000:8000 --env-file .env --network host graphiti-mcp

# Ή καθορίστε ρητά τις διευθύνσεις των εξωτερικών υπηρεσιών
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --env-file .env graphiti-mcp
```

## Δοκιμές

```bash
# Εκτέλεση όλων των δοκιμών (183, περίπου 1 δευτερόλεπτο)
uv run python -m pytest tests/

# Αναλυτική έξοδος
uv run python -m pytest tests/ -v

# Εκτέλεση μόνο συγκεκριμένων δοκιμών
uv run python -m pytest tests/test_content_preprocessor.py -v
uv run python -m pytest tests/test_new_features.py -v
uv run python -m pytest tests/test_unit.py -v
```

> **Σημείωση**: Οι 3 async δοκιμές στο `test_integration_manual.py` απαιτούν την εγκατάσταση του `pytest-asyncio`· όταν λείπει εμφανίζονται ως Failed αλλά δεν επηρεάζουν τις άλλες δοκιμές. Το `bench_deepseek_flash_vs_pro.py` είναι σενάριο benchmark απόδοσης, όχι δοκιμή μονάδας.

## Αντιμετώπιση προβλημάτων

### Αποτυχία σύνδεσης Neo4j

```bash
neo4j status                              # Έλεγχος κατάστασης υπηρεσίας
cypher-shell -u neo4j -p your_password    # Επιβεβαίωση ορθότητας κωδικού
curl http://localhost:7474                 # Επιβεβαίωση θύρας HTTP
```

Συνηθισμένες αιτίες:
- Το Neo4j δεν έχει εκκινήσει
- Λάθος κωδικός (`NEO4J_PASSWORD` στο `.env`)
- Η θύρα είναι κατειλημμένη ή φράσσεται από firewall

### Αποτυχία σύνδεσης LLM

**Λειτουργία Ollama:**
```bash
ollama serve                # Εκκίνηση υπηρεσίας Ollama
ollama list                 # Έλεγχος εγκατεστημένων μοντέλων
ollama pull qwen2.5:3b      # Εγκατάσταση μοντέλου που λείπει
```

Συνηθισμένες αιτίες: το Ollama δεν έχει εκκινήσει, το μοντέλο δεν είναι εγκατεστημένο, ανεπαρκής μνήμη GPU

**Λειτουργία GLM:**
- Επιβεβαιώστε ότι το `GLM_API_KEY` είναι σωστό
- Επιβεβαιώστε ότι `GLM_EMBEDDING_DIMENSIONS=768` (πρέπει να ταιριάζει με το διανυσματικό ευρετήριο Neo4j)
- Endpoint GLM API: `https://open.bigmodel.cn/api/paas/v4/`

**Λειτουργία GROQ:**
- Επιβεβαιώστε ότι το `GROQ_API_KEY` είναι σωστό
- Όταν το Rate Limit είναι συχνό, εξετάστε τη μετάβαση στη λειτουργία GLM
- Το GROQ δεν παρέχει Embedding, βεβαιωθείτε ότι ο ενσωματωτής Ollama είναι διαθέσιμος

**Λειτουργία OpenRouter:**
- Επιβεβαιώστε ότι το `OPENROUTER_API_KEY` είναι σωστό και το `OPENROUTER_MODEL` είναι έγκυρο ID μοντέλου (βλ. https://openrouter.ai/models)
- Δεν παρέχει Embedding, βεβαιωθείτε ότι ο ενσωματωτής Ollama είναι διαθέσιμος

**Λειτουργία DeepSeek:**
- Επιβεβαιώστε ότι το `DEEPSEEK_API_KEY` είναι σωστό
- Αν εμφανιστεί `Prompt must contain the word 'json'`: αυτή είναι σκληρή απαίτηση της λειτουργίας `json_object` του DeepSeek, ο πελάτης διαθέτει ενσωματωμένη εφεδρική προστασία· αν εξακολουθεί να εμφανίζεται, επιβεβαιώστε ότι χρησιμοποιείτε την πιο πρόσφατη έκδοση του `src/deepseek_client.py` και επανεκκινήστε την υπηρεσία
- Δεν παρέχει Embedding, βεβαιωθείτε ότι ο ενσωματωτής Ollama είναι διαθέσιμος

### Σφάλμα σύνδεσης MCP

Αν εμφανιστεί `Invalid request parameters` ή `Received request before initialization was complete`:

1. Επιβεβαιώστε ότι χρησιμοποιείτε τη λειτουργία μεταφοράς HTTP (**μην χρησιμοποιείτε SSE**)
2. Επιβεβαιώστε ότι ο πελάτης έχει ρυθμιστεί σε `"type": "http"`, `"url": "http://localhost:8000/mcp"`
3. Επανεκκινήστε την υπηρεσία: `pm2 restart graphiti-mcp-http --update-env`
4. Εκτελέστε `/mcp` στο Claude Code για επανασύνδεση

### Αργή ταχύτητα προσθήκης μνήμης

- **Ollama**: Ελέγξτε το μέγεθος του μοντέλου (το `qwen2.5:3b` είναι 5-10 φορές πιο γρήγορο από το `7b`), επιβεβαιώστε τη χρήση GPU (`ollama ps`)
- **GLM**: Κάθε add_episode απαιτεί 10-20+ διαδρομές δικτύου LLM, ~22s για σύντομο κείμενο είναι φυσιολογική τιμή
- **GROQ**: Το Rate Limit προκαλεί πολλές επαναλήψεις, αν η χρήση είναι συχνή συνιστάται η μετάβαση σε GLM ή Ollama
- Χρησιμοποιήστε `background=true` για να αποφύγετε το μπλοκάρισμα
- Μειώστε το `GRAPHITI_CHUNK_THRESHOLD` ώστε τα μεγάλα κείμενα να κατατμηθούν νωρίτερα

### Προβλήματα PM2

```bash
pm2 status                                        # Έλεγχος κατάστασης
pm2 logs graphiti-mcp-http --err --lines 50        # Καταγραφές σφαλμάτων
lsof -i :8000                                     # Έλεγχος κατάληψης θύρας
pm2 delete graphiti-mcp-http && pm2 start ecosystem.config.cjs  # Πλήρης επανεκκίνηση
```

## Εργαλεία ανάπτυξης και διάγνωσης

```bash
uv run python tools/status_report.py           # Ενοποιημένη αναφορά κατάστασης (Neo4j + Ollama + διαμόρφωση)
uv run python tools/validate_config.py         # Επαλήθευση πληρότητας .env και διαμόρφωσης
uv run python tools/performance_diagnose.py    # Διάγνωση απόδοσης LLM
uv run python tools/inspect_schema.py          # Έλεγχος ευρετηρίων και περιορισμών Neo4j
uv run python tools/migrate_embeddings.py      # Μετεγκατάσταση μοντέλου Embedding (αναπαραγωγή διανυσμάτων μετά την αλλαγή μοντέλου)
```

### Μετεγκατάσταση μοντέλου Embedding

Μετά την αλλαγή του μοντέλου embedding (π.χ. `nomic-embed-text` → `bge-m3`), μπορείτε να χρησιμοποιήσετε το εργαλείο μετεγκατάστασης για να αναπαράγετε όλα τα υπάρχοντα διανύσματα, εξασφαλίζοντας συνεπή ποιότητα αναζήτησης:

```bash
# Προεπισκόπηση του αριθμού που χρειάζεται μετεγκατάσταση
uv run python tools/migrate_embeddings.py --dry-run

# Πλήρης μετεγκατάσταση (υποστήριξη συνέχισης από σημείο διακοπής)
uv run python tools/migrate_embeddings.py

# Μετεγκατάσταση μόνο καθορισμένου group
uv run python tools/migrate_embeddings.py --group-id myproject

# Συνέχιση από σημείο διακοπής (επανεκτέλεση μετά από διακοπή)
uv run python tools/migrate_embeddings.py --resume
```

> **Συμβατότητα**: Το `bge-m3` έχει εγγενώς 1024 διαστάσεις, το σύστημα το περικόπτει αυτόματα σε 768 διαστάσεις για συμβατότητα με το υπάρχον διανυσματικό ευρετήριο Neo4j. Τα δεδομένα πριν και μετά τη μετεγκατάσταση μπορούν να συνυπάρχουν, αλλά συνιστάται η εκτέλεση πλήρους μετεγκατάστασης για βέλτιστη ποιότητα αναζήτησης.

## Τεκμηρίωση

- [Οδηγίες χρήσης εργαλείων](../使用工具的指令.md) — Οδηγός χρήσης εργαλείων MCP και βέλτιστες πρακτικές
- [Graphiti Memory Rules](../graphiti-memory-rules.md) — Επεξήγηση κανόνων μνήμης

## Άδεια χρήσης

MIT License
