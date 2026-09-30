                    USER
                      │
                      ▼
               NEXT.JS 16
                      │
          ┌───────────┼────────────┐
          │           │            │
       Upload      Documents      Chat
          │           │            │
          └───────────┼────────────┘
                      │
                      ▼
                   FASTAPI
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    PyMuPDF      SQLAlchemy        Ollama
       │              │              │
       ▼              ▼              ▼
    chunks      PostgreSQL       Llama 3.2
                    +
                 pgvector
                    │
                    ▼
                 Neon
